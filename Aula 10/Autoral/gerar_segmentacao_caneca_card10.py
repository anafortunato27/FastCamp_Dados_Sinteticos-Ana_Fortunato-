"""
Aluna: Ana Clara Fortunato de Souza.

Gera imagens RGB e máscaras automáticas da caneca para o Relatório 10.

O script reaproveita a lógica do Card 9 e produz quatro exemplos:
empty, mostly_empty, half_full e full.

Arquivos gerados em segmentacao_caneca/:
    imagens_rgb/
    mascaras_caneca/
    mascaras_liquido/

Uso no Blender:
1. Coloque este script e tea_mug.fbx na mesma pasta.
2. Abra o Blender e acesse a aba Scripting.
3. Abra este arquivo e clique em Run Script.
4. Aguarde a mensagem "CARD 10 CONCLUÍDO" no console.

Observação: os arquivos de máscara criados pelo nó File Output recebem o
número do frame no final do nome. Isso é normal no Compositor do Blender.
"""

import bpy
import math
from pathlib import Path
from mathutils import Vector


CLASSES = {
    "empty": 0.02,
    "mostly_empty": 0.28,
    "half_full": 0.55,
    "full": 0.82,
}

RESOLUCAO = 512
PASS_INDEX_CANECA = 1
PASS_INDEX_LIQUIDO = 2


def pasta_do_script():
    # Quando um script está armazenado dentro de um arquivo .blend, o Blender
    # pode montar __file__ como "arquivo.blend/script.py". Esse caminho não é
    # uma pasta real. Por isso, a pasta do .blend salvo tem prioridade.
    if bpy.data.filepath:
        return Path(bpy.data.filepath).resolve().parent

    try:
        caminho_script = Path(__file__).resolve()
        if caminho_script.parent.exists():
            return caminho_script.parent
    except NameError:
        pass

    return Path.cwd()


BASE_DIR = pasta_do_script()
SAIDA_DIR = BASE_DIR / "segmentacao_caneca"


def localizar_fbx():
    """Aceita tanto tea_mug.fbx quanto nomes como tea_mug(1).fbx."""
    caminho_padrao = BASE_DIR / "tea_mug.fbx"
    if caminho_padrao.exists():
        return caminho_padrao

    candidatos = sorted(BASE_DIR.glob("tea_mug*.fbx"))
    if candidatos:
        return candidatos[0]

    raise FileNotFoundError(
        "Nenhum arquivo tea_mug*.fbx foi encontrado na pasta: "
        f"{BASE_DIR}. Coloque o FBX ao lado do arquivo .blend."
    )


def limpar_cena():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for bloco in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for item in list(bloco):
            if item.users == 0:
                bloco.remove(item)


def importar_fbx(caminho):
    antes = set(bpy.context.scene.objects)

    # O novo operador wm.fbx_import só existe de fato no Blender 4.3+.
    # Em versões antigas, hasattr() pode retornar um falso positivo para
    # operadores dinâmicos do bpy, por isso a versão é verificada diretamente.
    if bpy.app.version >= (4, 3, 0):
        bpy.ops.wm.fbx_import(filepath=str(caminho))
    else:
        bpy.ops.import_scene.fbx(filepath=str(caminho))

    importados = [
        obj for obj in bpy.context.scene.objects
        if obj not in antes and obj.type == "MESH"
    ]

    if not importados:
        raise RuntimeError("O FBX foi importado, mas nenhuma malha foi encontrada.")

    for objeto in importados:
        objeto.pass_index = PASS_INDEX_CANECA

    return importados


def limites_mundo(objetos):
    pontos = [
        objeto.matrix_world @ Vector(canto)
        for objeto in objetos
        for canto in objeto.bound_box
    ]
    minimo = Vector((
        min(p.x for p in pontos),
        min(p.y for p in pontos),
        min(p.z for p in pontos),
    ))
    maximo = Vector((
        max(p.x for p in pontos),
        max(p.y for p in pontos),
        max(p.z for p in pontos),
    ))
    return minimo, maximo


def normalizar_caneca(objetos):
    minimo, maximo = limites_mundo(objetos)
    tamanho = max(
        maximo.x - minimo.x,
        maximo.y - minimo.y,
        maximo.z - minimo.z,
    )
    escala = 2.4 / tamanho
    centro = (minimo + maximo) / 2

    for objeto in objetos:
        objeto.location -= centro
        objeto.scale *= escala

    bpy.context.view_layer.update()
    minimo, _ = limites_mundo(objetos)

    for objeto in objetos:
        objeto.location.z -= minimo.z

    bpy.context.view_layer.update()
    return limites_mundo(objetos)


def material_principled(nome, cor, metallic=0.0, roughness=0.45):
    material = bpy.data.materials.new(nome)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = cor
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def criar_estudio():
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    piso = bpy.context.object
    piso.name = "Piso_Estudio"
    piso.pass_index = 0
    piso.data.materials.append(
        material_principled(
            "Material_Piso",
            (0.72, 0.76, 0.82, 1.0),
            roughness=0.65,
        )
    )

    bpy.ops.mesh.primitive_plane_add(
        size=12,
        location=(0, 3.2, 3.0),
        rotation=(math.radians(90), 0, 0),
    )
    fundo = bpy.context.object
    fundo.name = "Fundo_Estudio"
    fundo.pass_index = 0
    fundo.data.materials.append(
        material_principled(
            "Material_Fundo",
            (0.82, 0.86, 0.92, 1.0),
            roughness=0.80,
        )
    )


def criar_liquido(minimo, maximo):
    largura = maximo.x - minimo.x
    profundidade = maximo.y - minimo.y
    altura_caneca = maximo.z - minimo.z
    raio = max(0.12, min(largura, profundidade) * 0.30)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=raio,
        depth=0.08,
        location=(0, 0, minimo.z + altura_caneca * 0.18),
    )
    liquido = bpy.context.object
    liquido.name = "Liquido_Sintetico"
    liquido.pass_index = PASS_INDEX_LIQUIDO

    material = material_principled(
        "Material_Liquido",
        (0.22, 0.055, 0.012, 1.0),
        roughness=0.18,
    )
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.15
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.15

    liquido.data.materials.append(material)
    liquido["base_z"] = minimo.z + altura_caneca * 0.14
    liquido["altura_util"] = altura_caneca * 0.72
    return liquido


def criar_camera_e_luzes(altura_objeto):
    bpy.ops.object.empty_add(
        type="PLAIN_AXES",
        location=(0, 0, altura_objeto * 0.48),
    )
    alvo = bpy.context.object
    alvo.name = "Alvo_Caneca"

    # Posição fixa para facilitar a comparação entre os níveis.
    bpy.ops.object.camera_add(location=(4.2, -4.2, 3.2))
    camera = bpy.context.object
    camera.name = "Camera_Segmentacao"
    camera.data.lens = 52
    camera.data.clip_start = 0.02

    rastreamento = camera.constraints.new(type="TRACK_TO")
    rastreamento.target = alvo
    rastreamento.track_axis = "TRACK_NEGATIVE_Z"
    rastreamento.up_axis = "UP_Y"
    bpy.context.scene.camera = camera

    configuracoes = (
        ("Softbox_Principal", (3.0, -2.8, 4.5), 900, 3.0),
        ("Luz_Preenchimento", (-3.0, -1.0, 2.8), 500, 2.5),
    )

    for nome, local, energia, tamanho in configuracoes:
        bpy.ops.object.light_add(type="AREA", location=local)
        luz = bpy.context.object
        luz.name = nome
        luz.data.energy = energia
        luz.data.shape = "DISK"
        luz.data.size = tamanho

        restricao = luz.constraints.new(type="TRACK_TO")
        restricao.target = alvo
        restricao.track_axis = "TRACK_NEGATIVE_Z"
        restricao.up_axis = "UP_Y"


def configurar_render():
    cena = bpy.context.scene

    # Mantém compatibilidade com Blender 3.x e 4.x.
    try:
        cena.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        cena.render.engine = "BLENDER_EEVEE"

    cena.render.resolution_x = RESOLUCAO
    cena.render.resolution_y = RESOLUCAO
    cena.render.resolution_percentage = 100
    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_mode = "RGBA"
    cena.render.image_settings.color_depth = "8"
    cena.render.film_transparent = False
    cena.render.use_file_extension = True
    cena.world.color = (0.055, 0.07, 0.10)

    # Ativa a saída IndexOB usada pelos nós ID Mask.
    bpy.context.view_layer.use_pass_object_index = True


def novo_no_saida(arvore, nome, pasta_relativa, posicao):
    no = arvore.nodes.new("CompositorNodeOutputFile")
    no.name = nome
    no.label = nome
    no.location = posicao
    no.base_path = str(SAIDA_DIR)
    no.file_slots[0].path = pasta_relativa
    no.format.file_format = "PNG"
    no.format.color_mode = "BW"
    no.format.color_depth = "8"
    return no


def configurar_compositor():
    cena = bpy.context.scene
    cena.use_nodes = True
    arvore = cena.node_tree
    arvore.nodes.clear()

    render_layers = arvore.nodes.new("CompositorNodeRLayers")
    render_layers.name = "Render Layers"
    render_layers.location = (-520, 80)

    composite = arvore.nodes.new("CompositorNodeComposite")
    composite.location = (240, 260)
    arvore.links.new(render_layers.outputs["Image"], composite.inputs["Image"])

    mascara_caneca = arvore.nodes.new("CompositorNodeIDMask")
    mascara_caneca.name = "ID Mask - Caneca"
    mascara_caneca.label = "Caneca - índice 1"
    mascara_caneca.index = PASS_INDEX_CANECA
    mascara_caneca.location = (-220, 40)
    if hasattr(mascara_caneca, "use_antialiasing"):
        mascara_caneca.use_antialiasing = False

    mascara_liquido = arvore.nodes.new("CompositorNodeIDMask")
    mascara_liquido.name = "ID Mask - Liquido"
    mascara_liquido.label = "Líquido - índice 2"
    mascara_liquido.index = PASS_INDEX_LIQUIDO
    mascara_liquido.location = (-220, -180)
    if hasattr(mascara_liquido, "use_antialiasing"):
        mascara_liquido.use_antialiasing = False

    saida_caneca = novo_no_saida(
        arvore,
        "Saída - Máscara da Caneca",
        "mascaras_caneca/caneca_",
        (260, 40),
    )
    saida_liquido = novo_no_saida(
        arvore,
        "Saída - Máscara do Líquido",
        "mascaras_liquido/liquido_",
        (260, -180),
    )

    arvore.links.new(
        render_layers.outputs["IndexOB"],
        mascara_caneca.inputs["ID value"],
    )
    arvore.links.new(
        render_layers.outputs["IndexOB"],
        mascara_liquido.inputs["ID value"],
    )
    arvore.links.new(mascara_caneca.outputs["Alpha"], saida_caneca.inputs[0])
    arvore.links.new(mascara_liquido.outputs["Alpha"], saida_liquido.inputs[0])

    return saida_caneca, saida_liquido


def ajustar_nivel_liquido(liquido, classe, nivel):
    altura = max(0.025, liquido["altura_util"] * nivel)
    liquido.dimensions.z = altura
    liquido.location.z = liquido["base_z"] + altura / 2
    liquido.hide_render = classe == "empty"
    liquido.hide_viewport = classe == "empty"
    bpy.context.view_layer.update()


def gerar_exemplos(liquido, saida_caneca, saida_liquido):
    cena = bpy.context.scene
    pasta_rgb = SAIDA_DIR / "imagens_rgb"
    pasta_rgb.mkdir(parents=True, exist_ok=True)
    (SAIDA_DIR / "mascaras_caneca").mkdir(parents=True, exist_ok=True)
    (SAIDA_DIR / "mascaras_liquido").mkdir(parents=True, exist_ok=True)

    for frame, (classe, nivel) in enumerate(CLASSES.items(), start=1):
        cena.frame_set(frame)
        ajustar_nivel_liquido(liquido, classe, nivel)

        # O nome da classe é incluído antes do número automático do frame.
        saida_caneca.file_slots[0].path = (
            f"mascaras_caneca/{classe}_caneca_"
        )
        saida_liquido.file_slots[0].path = (
            f"mascaras_liquido/{classe}_liquido_"
        )

        cena.render.filepath = str(pasta_rgb / f"{classe}.png")
        bpy.ops.render.render(write_still=True)
        print(f"Gerado: {classe}")


def main():
    fbx_path = localizar_fbx()
    limpar_cena()

    objetos_caneca = importar_fbx(fbx_path)
    minimo, maximo = normalizar_caneca(objetos_caneca)
    criar_estudio()
    liquido = criar_liquido(minimo, maximo)
    criar_camera_e_luzes(maximo.z - minimo.z)
    configurar_render()
    saida_caneca, saida_liquido = configurar_compositor()

    gerar_exemplos(liquido, saida_caneca, saida_liquido)

    arquivo_blend = BASE_DIR / "cena_caneca_segmentacao_card10.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(arquivo_blend))

    print("=" * 60)
    print("CARD 10 CONCLUÍDO")
    print(f"Resultados: {SAIDA_DIR}")
    print(f"Cena salva em: {arquivo_blend}")
    print("=" * 60)


if __name__ == "__main__":
    main()