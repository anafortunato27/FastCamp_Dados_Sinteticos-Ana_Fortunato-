# ============================================================
# DATASET SINTÉTICO: CUBO, ESFERA E CONE
# Aluna: Ana Clara Fortunato de Souza
# Gera imagens organizadas em train/val/test por classe.
# ============================================================

import bpy
import math
import random
from pathlib import Path
from mathutils import Vector

# -----------------------------
# CONFIGURAÇÕES
# -----------------------------
SEED = 42
random.seed(SEED)

# Quantidade de imagens por classe
QUANTIDADES = {
    "train": 30,
    "val": 10,
    "test": 5,
}

# Para um teste rápido, use:
# QUANTIDADES = {"train": 3, "val": 2, "test": 1}

RESOLUCAO = 224
PASTA_DATASET = "dataset_cubo_esfera_cone"

CLASSES = {
    "cubo": "Cubo",
    "esfera": "Esfera",
    "cone": "Cone",
}

# -----------------------------
# FUNÇÕES AUXILIARES
# -----------------------------
def limpar_cena():
    """Remove todos os objetos da cena atual."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Remove materiais antigos sem usuários
    for material in list(bpy.data.materials):
        if material.users == 0:
            bpy.data.materials.remove(material)


def criar_material(nome, cor=(0.2, 0.4, 0.8, 1.0), roughness=0.4):
    """Cria um material com nós e retorna o material."""
    material = bpy.data.materials.new(name=nome)
    material.use_nodes = True

    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = cor
        principled.inputs["Roughness"].default_value = roughness

    return material


def aplicar_material(objeto, material):
    """Aplica um material ao objeto."""
    if len(objeto.data.materials) == 0:
        objeto.data.materials.append(material)
    else:
        objeto.data.materials[0] = material


def apontar_para(objeto, alvo=(0.0, 0.0, 0.8)):
    """Faz uma câmera ou luz apontar para um ponto."""
    direcao = Vector(alvo) - objeto.location
    objeto.rotation_euler = direcao.to_track_quat("-Z", "Y").to_euler()


def criar_objetos():
    """Cria cubo, esfera e cone."""
    objetos = {}

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1.0))
    cubo = bpy.context.active_object
    cubo.name = "Cubo"
    objetos["cubo"] = cubo

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=32,
        ring_count=16,
        radius=1.15,
        location=(0, 0, 1.15)
    )
    esfera = bpy.context.active_object
    esfera.name = "Esfera"
    bpy.ops.object.shade_smooth()
    objetos["esfera"] = esfera

    bpy.ops.mesh.primitive_cone_add(
        vertices=32,
        radius1=1.15,
        radius2=0.0,
        depth=2.3,
        location=(0, 0, 1.15)
    )
    cone = bpy.context.active_object
    cone.name = "Cone"
    objetos["cone"] = cone

    for chave, objeto in objetos.items():
        material = criar_material(
            nome=f"Material_{chave}",
            cor=(0.15, 0.35, 0.8, 1.0),
            roughness=0.38,
        )
        aplicar_material(objeto, material)

    return objetos


def criar_estudio():
    """Cria chão, fundo, iluminação e câmera."""
    # Chão
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    chao = bpy.context.active_object
    chao.name = "Chao"
    aplicar_material(
        chao,
        criar_material("Material_Chao", (0.72, 0.72, 0.72, 1.0), 0.65)
    )

    # Parede de fundo
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 4.2, 5.0))
    fundo = bpy.context.active_object
    fundo.name = "Fundo"
    fundo.rotation_euler = (math.radians(90), 0, 0)
    aplicar_material(
        fundo,
        criar_material("Material_Fundo", (0.55, 0.55, 0.55, 1.0), 0.75)
    )

    # Luz principal
    bpy.ops.object.light_add(type="AREA", location=(4.5, -4.0, 6.0))
    luz_principal = bpy.context.active_object
    luz_principal.name = "Luz_Principal"
    luz_principal.data.energy = 900
    luz_principal.data.size = 5.0
    apontar_para(luz_principal)

    # Luz de preenchimento
    bpy.ops.object.light_add(type="AREA", location=(-4.0, -2.0, 3.5))
    luz_preenchimento = bpy.context.active_object
    luz_preenchimento.name = "Luz_Preenchimento"
    luz_preenchimento.data.energy = 500
    luz_preenchimento.data.size = 4.0
    apontar_para(luz_preenchimento)

    # Luz superior
    bpy.ops.object.light_add(type="AREA", location=(0.0, 1.0, 7.0))
    luz_superior = bpy.context.active_object
    luz_superior.name = "Luz_Superior"
    luz_superior.data.energy = 350
    luz_superior.data.size = 3.0
    apontar_para(luz_superior)

    # Câmera
    bpy.ops.object.camera_add(location=(6.8, -7.0, 5.0))
    camera = bpy.context.active_object
    camera.name = "Camera_Dataset"
    camera.data.lens = 52
    apontar_para(camera, alvo=(0.0, 0.0, 1.0))
    bpy.context.scene.camera = camera

    return camera


def configurar_render():
    """Configura o motor e o formato de renderização."""
    cena = bpy.context.scene

    # Blender 2.80+
    cena.render.engine = "BLENDER_EEVEE"

    cena.render.resolution_x = RESOLUCAO
    cena.render.resolution_y = RESOLUCAO
    cena.render.resolution_percentage = 100

    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_mode = "RGB"
    cena.render.film_transparent = False

    # Melhor qualidade visual no Eevee
    if hasattr(cena, "eevee"):
        cena.eevee.use_gtao = True
        cena.eevee.gtao_distance = 3
        cena.eevee.gtao_factor = 1.25
        cena.eevee.use_soft_shadows = True

    # Cor do mundo
    cena.world.color = (0.04, 0.04, 0.04)


def definir_visibilidade(objetos, classe_ativa):
    """Mantém somente o objeto da classe atual visível no render."""
    for classe, objeto in objetos.items():
        visivel = classe == classe_ativa
        objeto.hide_render = not visivel
        objeto.hide_viewport = not visivel


def randomizar_objeto(objeto):
    """Aplica variações controladas para manter o objeto reconhecível."""
    # Rotação
    objeto.rotation_euler = (
        random.uniform(math.radians(-22), math.radians(22)),
        random.uniform(math.radians(-22), math.radians(22)),
        random.uniform(0, 2 * math.pi),
    )

    # Pequena variação de posição
    objeto.location.x = random.uniform(-0.25, 0.25)
    objeto.location.y = random.uniform(-0.15, 0.18)

    # Mantém altura apropriada para cada objeto
    if objeto.name == "Cubo":
        objeto.location.z = 1.0
    else:
        objeto.location.z = 1.15

    # Pequena variação de escala
    escala = random.uniform(0.88, 1.08)
    objeto.scale = (escala, escala, escala)

    # Cor aleatória viva
    material = objeto.active_material
    if material and material.use_nodes:
        principled = material.node_tree.nodes.get("Principled BSDF")
        if principled:
            cor = (
                random.uniform(0.12, 0.90),
                random.uniform(0.12, 0.90),
                random.uniform(0.12, 0.90),
                1.0,
            )
            principled.inputs["Base Color"].default_value = cor
            principled.inputs["Roughness"].default_value = random.uniform(0.30, 0.55)


def criar_pastas(base):
    """Cria a estrutura train/val/test por classe."""
    for divisao in QUANTIDADES:
        for classe in CLASSES:
            (base / divisao / classe).mkdir(parents=True, exist_ok=True)


def gerar_dataset(objetos):
    """Executa as renderizações e salva as imagens."""
    # // significa a pasta onde o arquivo .blend está salvo.
    base = Path(bpy.path.abspath("//")) / PASTA_DATASET
    criar_pastas(base)

    total = sum(QUANTIDADES.values()) * len(CLASSES)
    atual = 0

    for divisao, quantidade in QUANTIDADES.items():
        for classe, nome_objeto in CLASSES.items():
            definir_visibilidade(objetos, classe)
            objeto = objetos[classe]

            for indice in range(quantidade):
                atual += 1
                randomizar_objeto(objeto)

                nome_arquivo = f"{classe}_{indice:04d}.png"
                caminho = base / divisao / classe / nome_arquivo

                bpy.context.scene.render.filepath = str(caminho)
                bpy.ops.render.render(write_still=True)

                print(
                    f"[{atual}/{total}] "
                    f"{divisao}/{classe}/{nome_arquivo}"
                )

    # Torna todos visíveis novamente no viewport
    for objeto in objetos.values():
        objeto.hide_render = False
        objeto.hide_viewport = False

    print("=" * 60)
    print("DATASET CONCLUÍDO!")
    print(f"Pasta: {base}")
    print(f"Total de imagens: {total}")
    print("=" * 60)


# -----------------------------
# EXECUÇÃO
# -----------------------------
limpar_cena()
objetos = criar_objetos()
criar_estudio()
configurar_render()
gerar_dataset(objetos)
