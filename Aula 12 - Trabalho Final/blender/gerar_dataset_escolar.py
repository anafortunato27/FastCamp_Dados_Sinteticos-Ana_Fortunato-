"""
Aluna: Ana Clara Fortunato de Souza.

Gera um dataset YOLO de lápis, borracha e apontador no Blender.

Uso:
1. Abra este arquivo em Blender > Scripting.
2. Clique em Run Script.

Saídas:
- dataset/{train,valid,test}/{images,labels}
- dataset/manifesto.csv
- blender/cena_materiais_escolares.blend
"""

import bpy
import csv
import math
import random
from pathlib import Path

from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


SEMENTE = 42
TOTAL_IMAGENS = 600
RESOLUCAO = 640
CLASSES = {"lapis": 0, "borracha": 1, "apontador": 2}
SPLITS = (("train", 420), ("valid", 90), ("test", 90))
MARGEM = 0.035
TENTATIVAS_POSICAO = 80
RENDER_ENGINE = "BLENDER_EEVEE_NEXT"


def raiz_projeto():
    caminho = Path(__file__).resolve()
    return caminho.parent.parent


RAIZ = raiz_projeto()
DATASET = RAIZ / "dataset"


def limpar_cena():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for colecao in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                    bpy.data.cameras, bpy.data.lights):
        pass  # Mantém datablocks válidos durante a execução.


def material(nome, cor, metalico=0.0, rugosidade=0.45):
    mat = bpy.data.materials.get(nome) or bpy.data.materials.new(nome)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*cor, 1.0)
    bsdf.inputs["Metallic"].default_value = metalico
    bsdf.inputs["Roughness"].default_value = rugosidade
    return mat


def aplicar_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def adicionar_cubo(nome, local, escala, mat, bevel=0.08):
    bpy.ops.mesh.primitive_cube_add(location=local)
    obj = bpy.context.object
    obj.name = nome
    obj.scale = escala
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("Bordas", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    aplicar_material(obj, mat)
    return obj


def criar_lapis():
    partes = []
    madeira = material("Madeira", (0.72, 0.44, 0.18), rugosidade=0.6)
    grafite = material("Grafite", (0.025, 0.025, 0.03), metalico=0.1, rugosidade=0.3)
    corpo = material("CorLapis", (0.05, 0.28, 0.85), rugosidade=0.35)
    metal = material("MetalLapis", (0.55, 0.58, 0.62), metalico=0.85, rugosidade=0.2)
    borracha = material("BorrachaLapis", (0.95, 0.42, 0.55), rugosidade=0.55)

    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.17, depth=3.4,
                                        location=(0, 0, 0.32), rotation=(0, math.pi / 2, 0))
    partes.append(bpy.context.object)
    aplicar_material(partes[-1], corpo)
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.17, radius2=0.04, depth=0.55,
                                    location=(1.975, 0, 0.32), rotation=(0, math.pi / 2, 0))
    partes.append(bpy.context.object)
    aplicar_material(partes[-1], madeira)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.042, radius2=0.0, depth=0.16,
                                    location=(2.33, 0, 0.32), rotation=(0, math.pi / 2, 0))
    partes.append(bpy.context.object)
    aplicar_material(partes[-1], grafite)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.18, depth=0.25,
                                        location=(-1.825, 0, 0.32), rotation=(0, math.pi / 2, 0))
    partes.append(bpy.context.object)
    aplicar_material(partes[-1], metal)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.17, depth=0.32,
                                        location=(-2.11, 0, 0.32), rotation=(0, math.pi / 2, 0))
    partes.append(bpy.context.object)
    aplicar_material(partes[-1], borracha)
    return unir_objetos(partes, "lapis")


def criar_borracha():
    rosa = material("BorrachaRosa", (0.96, 0.24, 0.38), rugosidade=0.62)
    faixa = material("FaixaBorracha", (0.95, 0.82, 0.18), rugosidade=0.5)
    corpo = adicionar_cubo("corpo_borracha", (0, 0, 0.32), (1.15, 0.58, 0.28), rosa, 0.16)
    cinta = adicionar_cubo("cinta_borracha", (0, 0, 0.33), (0.38, 0.61, 0.30), faixa, 0.05)
    return unir_objetos([corpo, cinta], "borracha")


def criar_apontador():
    partes = []
    azul = material("ApontadorAzul", (0.06, 0.62, 0.68), rugosidade=0.38)
    metal = material("Lamina", (0.62, 0.66, 0.70), metalico=0.9, rugosidade=0.18)
    escuro = material("Furo", (0.015, 0.02, 0.025), rugosidade=0.8)
    partes.append(adicionar_cubo("corpo_apontador", (0, 0, 0.38), (0.72, 0.52, 0.34), azul, 0.16))
    partes.append(adicionar_cubo("lamina_apontador", (0.02, 0, 0.745), (0.55, 0.20, 0.025), metal, 0.025))
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.20, depth=0.04,
                                        location=(-0.73, 0, 0.39), rotation=(0, math.pi / 2, 0))
    partes.append(bpy.context.object)
    aplicar_material(partes[-1], escuro)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.055, depth=0.07,
                                        location=(0.12, 0, 0.79))
    partes.append(bpy.context.object)
    aplicar_material(partes[-1], escuro)
    return unir_objetos(partes, "apontador")


def unir_objetos(partes, nome):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in partes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = partes[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = nome
    obj["classe"] = nome
    obj.hide_render = True
    obj.hide_viewport = True
    return obj


def criar_cena():
    limpar_cena()
    fundo = material("Fundo", (0.55, 0.58, 0.62), rugosidade=0.7)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    plano = bpy.context.object
    plano.name = "Fundo"
    aplicar_material(plano, fundo)

    bpy.ops.object.camera_add(location=(0, 0, 10))
    camera = bpy.context.object
    camera.name = "CameraDataset"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 9.2
    bpy.context.scene.camera = camera

    luzes = []
    for nome, local, energia, tamanho in (
        ("LuzPrincipal", (4, -4, 8), 900, 5.0),
        ("LuzPreenchimento", (-4, 2, 6), 500, 4.0),
        ("LuzLateral", (1, 5, 5), 350, 3.0),
    ):
        bpy.ops.object.light_add(type="AREA", location=local)
        luz = bpy.context.object
        luz.name = nome
        luz.data.energy = energia
        luz.data.shape = "DISK"
        luz.data.size = tamanho
        luzes.append(luz)

    modelos = {"lapis": criar_lapis(), "borracha": criar_borracha(),
               "apontador": criar_apontador()}
    return plano, camera, luzes, modelos


def olhar_para(obj, alvo=Vector((0, 0, 0))):
    obj.rotation_euler = (alvo - obj.location).to_track_quat("-Z", "Y").to_euler()


def preparar_pastas():
    for split, _ in SPLITS:
        for tipo in ("images", "labels"):
            (DATASET / split / tipo).mkdir(parents=True, exist_ok=True)


def split_por_indice(indice):
    acumulado = 0
    for split, quantidade in SPLITS:
        acumulado += quantidade
        if indice < acumulado:
            return split
    raise ValueError("Índice fora do total configurado")


def sobrepoe(posicao, ocupados, raio):
    return any((Vector(posicao[:2]) - Vector(p[:2])).length < raio + r for p, r in ocupados)


def instanciar(modelo, classe, indice, ocupados):
    obj = modelo.copy()
    obj.data = modelo.data.copy()
    bpy.context.collection.objects.link(obj)
    obj.name = f"{classe}_{indice:02d}"
    obj.hide_render = False
    obj.hide_viewport = False
    escala = random.uniform(0.72, 1.15)
    obj.scale = (escala, escala, escala)
    raio = {"lapis": 1.75, "borracha": 1.15, "apontador": 0.95}[classe] * escala
    for _ in range(TENTATIVAS_POSICAO):
        pos = (random.uniform(-3.25, 3.25), random.uniform(-3.25, 3.25), 0)
        if not sobrepoe(pos, ocupados, raio * 0.72):
            break
    else:
        pos = (random.uniform(-2.5, 2.5), random.uniform(-2.5, 2.5), 0)
    ocupados.append((pos, raio * 0.72))
    obj.location.x, obj.location.y = pos[0], pos[1]
    obj.rotation_euler[2] = random.uniform(0, 2 * math.pi)
    obj.rotation_euler[0] = random.uniform(-0.05, 0.05)
    obj.rotation_euler[1] = random.uniform(-0.05, 0.05)
    return obj


def bbox_yolo(cena, camera, obj):
    coords = []
    for canto in obj.bound_box:
        mundo = obj.matrix_world @ Vector(canto)
        coords.append(world_to_camera_view(cena, camera, mundo))
    xs = [p.x for p in coords if p.z > 0]
    ys = [p.y for p in coords if p.z > 0]
    if not xs or not ys:
        return None
    xmin, xmax = max(0.0, min(xs)), min(1.0, max(xs))
    ymin, ymax = max(0.0, min(ys)), min(1.0, max(ys))
    if xmin >= xmax or ymin >= ymax:
        return None
    largura, altura = xmax - xmin, ymax - ymin
    if largura < 0.012 or altura < 0.012:
        return None
    return ((xmin + xmax) / 2, 1 - (ymin + ymax) / 2, largura, altura)


def randomizar_ambiente(plano, camera, luzes):
    cores_fundo = (
        (0.82, 0.84, 0.88), (0.32, 0.39, 0.46), (0.74, 0.66, 0.52),
        (0.46, 0.60, 0.50), (0.67, 0.48, 0.42), (0.18, 0.22, 0.28),
    )
    cor = random.choice(cores_fundo)
    bsdf = plano.data.materials[0].node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*cor, 1.0)
    bsdf.inputs["Roughness"].default_value = random.uniform(0.5, 0.9)
    camera.location = (random.uniform(-0.65, 0.65), random.uniform(-0.65, 0.65),
                       random.uniform(9.0, 11.0))
    camera.data.ortho_scale = random.uniform(8.3, 9.8)
    olhar_para(camera, Vector((random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25), 0)))
    for luz in luzes:
        luz.data.energy = random.uniform(250, 1150)
        luz.data.color = (random.uniform(0.82, 1.0), random.uniform(0.82, 1.0),
                          random.uniform(0.82, 1.0))
    bpy.context.scene.world.color = tuple(random.uniform(0.025, 0.12) for _ in range(3))


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
    cena.render.image_settings.color_mode = "RGB"
    cena.render.film_transparent = False
    cena.render.image_settings.color_depth = "8"
    cena.view_settings.look = "AgX - Medium High Contrast" if bpy.app.version >= (4, 0, 0) else "Medium High Contrast"
    return cena


def selecionar_classes(indice):
    # Ciclo garante que cada classe apareça com frequência semelhante.
    obrigatoria = list(CLASSES)[indice % len(CLASSES)]
    quantidade = random.choices((1, 2, 3), weights=(0.15, 0.45, 0.40), k=1)[0]
    restantes = [c for c in CLASSES if c != obrigatoria]
    return [obrigatoria] + random.sample(restantes, quantidade - 1)


def gerar():
    random.seed(SEMENTE)
    preparar_pastas()
    plano, camera, luzes, modelos = criar_cena()
    cena = configurar_render()
    manifesto = DATASET / "manifesto.csv"
    with manifesto.open("w", newline="", encoding="utf-8") as arq:
        writer = csv.writer(arq)
        writer.writerow(["arquivo", "split", "classes", "objetos", "ortho_scale"])
        for indice in range(TOTAL_IMAGENS):
            split = split_por_indice(indice)
            randomizar_ambiente(plano, camera, luzes)
            ocupados, objetos = [], []
            classes = selecionar_classes(indice)
            for pos, classe in enumerate(classes):
                objetos.append(instanciar(modelos[classe], classe, pos, ocupados))
            bpy.context.view_layer.update()

            linhas = []
            for obj in objetos:
                bbox = bbox_yolo(cena, camera, obj)
                if bbox:
                    linhas.append(f"{CLASSES[obj['classe']]} " + " ".join(f"{v:.6f}" for v in bbox))
            if len(linhas) != len(objetos):
                for obj in objetos:
                    bpy.data.objects.remove(obj, do_unlink=True)
                raise RuntimeError(f"Objeto fora da câmera na amostra {indice}; ajuste os limites.")

            nome = f"escolar_{indice:04d}"
            cena.render.filepath = str(DATASET / split / "images" / f"{nome}.png")
            bpy.ops.render.render(write_still=True)
            (DATASET / split / "labels" / f"{nome}.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")
            writer.writerow([nome, split, ";".join(classes), len(objetos), f"{camera.data.ortho_scale:.3f}"])
            for obj in objetos:
                bpy.data.objects.remove(obj, do_unlink=True)
            if (indice + 1) % 25 == 0:
                print(f"Geradas {indice + 1}/{TOTAL_IMAGENS} imagens")

    bpy.ops.wm.save_as_mainfile(filepath=str(RAIZ / "blender" / "cena_materiais_escolares.blend"))
    print(f"Dataset concluído em: {DATASET}")


if __name__ == "__main__":
    gerar()

