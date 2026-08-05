"""Gera um dataset sintético de uma caneca com quatro níveis de líquido.

Uso no Blender:
1. Coloque tea_mug.fbx na mesma pasta deste script.
2. Abra Blender > Scripting > Open e selecione este arquivo.
3. Clique em Run Script.

As imagens serão criadas em dataset_caneca/{train,val,test}/{classe}.
"""

import bpy
import math
import random
from pathlib import Path
from mathutils import Vector


SEMENTE = 42
IMAGENS_POR_CLASSE = {"train": 60, "val": 15, "test": 10}
CLASSES = {
    "empty": 0.02,
    "mostly_empty": 0.28,
    "half_full": 0.55,
    "full": 0.82,
}
RESOLUCAO = 224
RENDER_ENGINE = "BLENDER_EEVEE_NEXT"  # use "BLENDER_EEVEE" no Blender 3.x


def pasta_do_script():
    if bpy.data.filepath:
        return Path(bpy.data.filepath).parent
    try:
        return Path(__file__).resolve().parent
    except NameError:
        return Path.cwd()


BASE_DIR = pasta_do_script()
FBX_PATH = BASE_DIR / "tea_mug.fbx"
DATASET_DIR = BASE_DIR / "dataset_caneca"


def limpar_cena():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for bloco in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                  bpy.data.cameras, bpy.data.lights):
        for item in list(bloco):
            if item.users == 0:
                bloco.remove(item)


def importar_fbx(caminho):
    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}. Coloque tea_mug.fbx junto do script."
        )
    antes = set(bpy.context.scene.objects)
    if hasattr(bpy.ops.wm, "fbx_import"):
        bpy.ops.wm.fbx_import(filepath=str(caminho))
    else:
        bpy.ops.import_scene.fbx(filepath=str(caminho))
    importados = [obj for obj in bpy.context.scene.objects if obj not in antes]
    malhas = [obj for obj in importados if obj.type == "MESH"]
    if not malhas:
        raise RuntimeError("O FBX foi importado, mas nenhuma malha foi encontrada.")
    return malhas


def limites_mundo(objetos):
    pontos = [obj.matrix_world @ Vector(canto) for obj in objetos for canto in obj.bound_box]
    minimo = Vector((min(p.x for p in pontos), min(p.y for p in pontos), min(p.z for p in pontos)))
    maximo = Vector((max(p.x for p in pontos), max(p.y for p in pontos), max(p.z for p in pontos)))
    return minimo, maximo


def normalizar_caneca(objetos):
    minimo, maximo = limites_mundo(objetos)
    tamanho = max(maximo.x - minimo.x, maximo.y - minimo.y, maximo.z - minimo.z)
    escala = 2.4 / tamanho
    centro = (minimo + maximo) / 2
    for obj in objetos:
        obj.location -= centro
        obj.scale *= escala
    bpy.context.view_layer.update()
    minimo, maximo = limites_mundo(objetos)
    deslocamento_z = -minimo.z
    for obj in objetos:
        obj.location.z += deslocamento_z
    bpy.context.view_layer.update()
    return limites_mundo(objetos)


def material_principled(nome, cor, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = cor
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def criar_estudio():
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    piso = bpy.context.object
    piso.name = "Piso_Estudio"
    piso.data.materials.append(material_principled("Material_Piso", (0.72, 0.76, 0.82, 1), roughness=0.65))

    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 3.2, 3.0), rotation=(math.radians(90), 0, 0))
    fundo = bpy.context.object
    fundo.name = "Fundo_Estudio"
    fundo.data.materials.append(material_principled("Material_Fundo", (0.82, 0.86, 0.92, 1), roughness=0.8))


def criar_liquido(minimo, maximo):
    largura = maximo.x - minimo.x
    profundidade = maximo.y - minimo.y
    altura = maximo.z - minimo.z
    raio = max(0.12, min(largura, profundidade) * 0.30)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=raio, depth=0.08,
                                       location=(0, 0, minimo.z + altura * 0.18))
    liquido = bpy.context.object
    liquido.name = "Liquido_Sintetico"
    mat = material_principled("Material_Liquido", (0.22, 0.055, 0.012, 1), roughness=0.18)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.15
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.15
    liquido.data.materials.append(mat)
    liquido["base_z"] = minimo.z + altura * 0.14
    liquido["altura_util"] = altura * 0.72
    return liquido


def criar_camera_e_luzes(altura_objeto):
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, altura_objeto * 0.48))
    alvo = bpy.context.object
    alvo.name = "Alvo_Caneca"

    bpy.ops.object.camera_add(location=(4.2, -4.2, 3.2))
    camera = bpy.context.object
    camera.name = "Camera_Dataset"
    camera.data.lens = 52
    camera.data.clip_start = 0.02
    track = camera.constraints.new(type="TRACK_TO")
    track.target = alvo
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    bpy.context.scene.camera = camera

    for nome, local, energia, tamanho in (
        ("Softbox_Principal", (3.0, -2.8, 4.5), 900, 3.0),
        ("Luz_Preenchimento", (-3.0, -1.0, 2.8), 500, 2.5),
    ):
        bpy.ops.object.light_add(type="AREA", location=local)
        luz = bpy.context.object
        luz.name = nome
        luz.data.energy = energia
        luz.data.shape = "DISK"
        luz.data.size = tamanho
        c = luz.constraints.new(type="TRACK_TO")
        c.target = alvo
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
    return camera, alvo


def configurar_render():
    cena = bpy.context.scene
    try:
        cena.render.engine = RENDER_ENGINE
    except TypeError:
        cena.render.engine = "BLENDER_EEVEE"
    cena.render.resolution_x = RESOLUCAO
    cena.render.resolution_y = RESOLUCAO
    cena.render.resolution_percentage = 100
    cena.render.image_settings.file_format = "PNG"
    cena.render.film_transparent = False
    cena.render.image_settings.color_mode = "RGBA"
    cena.world.color = (0.055, 0.07, 0.10)
    cena.render.use_file_extension = True


def variar_cena(camera, liquido, classe, nivel, indice):
    angulo = random.uniform(-math.pi, math.pi)
    raio = random.uniform(4.2, 5.0)
    camera.location.x = raio * math.cos(angulo)
    camera.location.y = raio * math.sin(angulo)
    camera.location.z = random.uniform(2.2, 4.0)
    camera.data.lens = random.uniform(48, 58)

    altura = max(0.025, liquido["altura_util"] * nivel)
    liquido.dimensions.z = altura
    liquido.location.z = liquido["base_z"] + altura / 2
    liquido.hide_render = classe == "empty"
    mat = liquido.data.materials[0]
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    tom = random.uniform(0.0, 0.035)
    bsdf.inputs["Base Color"].default_value = (
        random.uniform(0.16, 0.32) + tom,
        random.uniform(0.025, 0.085),
        random.uniform(0.008, 0.025), 1.0
    )
    bpy.context.view_layer.update()


def gerar_dataset(camera, liquido):
    random.seed(SEMENTE)
    total = 0
    for divisao, quantidade in IMAGENS_POR_CLASSE.items():
        for classe, nivel in CLASSES.items():
            destino = DATASET_DIR / divisao / classe
            destino.mkdir(parents=True, exist_ok=True)
            for indice in range(quantidade):
                variar_cena(camera, liquido, classe, nivel, indice)
                arquivo = destino / f"{classe}_{indice:04d}.png"
                bpy.context.scene.render.filepath = str(arquivo)
                bpy.ops.render.render(write_still=True)
                total += 1
                print(f"[{total}] {arquivo}")
    return total


def main():
    limpar_cena()
    objetos = importar_fbx(FBX_PATH)
    minimo, maximo = normalizar_caneca(objetos)
    criar_estudio()
    liquido = criar_liquido(minimo, maximo)
    camera, _ = criar_camera_e_luzes(maximo.z - minimo.z)
    configurar_render()
    arquivo_blend = BASE_DIR / "cena_caneca_dataset.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(arquivo_blend))
    total = gerar_dataset(camera, liquido)
    print(f"Concluído: {total} imagens em {DATASET_DIR}")
    print(f"Cena salva em {arquivo_blend}")


if __name__ == "__main__":
    main()
