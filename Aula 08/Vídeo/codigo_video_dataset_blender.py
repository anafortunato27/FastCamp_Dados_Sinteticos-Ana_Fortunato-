"""
Aluna: Ana Clara Fortunato de Souza
Dataset sintético no Blender: cubo, esfera e cone.

Baseado na lógica apresentada em "3D Rendered Datasets in Blender for
Beginners, Part 2": ocultar classes, randomizar o objeto, renderizar em loop
e organizar as imagens em treino, validação e teste.

Como usar:
1. Abra o Blender e salve o arquivo .blend.
2. Vá para Scripting > New.
3. Abra este arquivo e pressione Alt+P (Run Script).

O dataset será criado ao lado do arquivo .blend. Caso o .blend ainda não
tenha sido salvo, ele será criado na pasta temporária do sistema.
"""

import bpy
import math
import random
import time
from pathlib import Path
from mathutils import Color, Vector


def gerar_figura_1(objetos, pasta_saida):
    """Gera uma imagem inicial com cubo, esfera e cone lado a lado."""
    cena = bpy.context.scene

    # Deixa todos os objetos visíveis
    for objeto in objetos.values():
        objeto.hide_render = False
        objeto.hide_viewport = False
        objeto.rotation_euler = (0, 0, 0)
        objeto.scale = (1, 1, 1)

    # Posiciona os objetos lado a lado
    objetos["cubo"].location = (-2.5, 0, 1.2)
    objetos["esfera"].location = (0, 0, 1.2)
    objetos["cone"].location = (2.5, 0, 1.2)

    # Define cores fixas para a imagem inicial
    materiais_cores = {
        "cubo": (0.05, 0.20, 0.80, 1.0),      # azul
        "esfera": (0.10, 0.65, 0.20, 1.0),   # verde
        "cone": (1.00, 0.25, 0.05, 1.0),     # laranja
    }

    for nome, cor in materiais_cores.items():
        material = objetos[nome].data.materials[0]
        principled = material.node_tree.nodes.get("Principled BSDF")
        principled.inputs["Base Color"].default_value = cor
        principled.inputs["Roughness"].default_value = 0.35

    # Ajusta a câmera para enquadrar os três objetos
    camera = bpy.data.objects["camera_dataset"]
    camera.location = (0, -11, 4.5)
    camera.data.lens = 50
    apontar_para(camera, ponto=(0, 0, 1.2))
    cena.camera = camera

    # Define onde a Figura 1 será salva
    caminho_figura = pasta_saida / "figura_1_cena_inicial.png"
    cena.render.filepath = str(caminho_figura)

    # Renderiza e salva
    bpy.ops.render.render(write_still=True)

    print("Figura 1 salva em: {}".format(caminho_figura))


# ---------------------------------------------------------------------------
# CONFIGURAÇÕES QUE VOCÊ PODE ALTERAR
# ---------------------------------------------------------------------------

SEMENTE_ALEATORIA = 42
RESOLUCAO = 224

# Quantidade de imagens POR CLASSE em cada divisão.
IMAGENS_POR_DIVISAO = {
    "train": 30,
    "val": 10,
    "test": 5,
}

NOMES_DOS_OBJETOS = ["cubo", "esfera", "cone"]
NOME_DA_PASTA = "dataset_cubo_esfera_cone"


# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------------------

def limpar_cena():
    """Remove todos os objetos existentes da cena."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Remove dados órfãos criados ao apagar os objetos.
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def criar_material(nome, cor=(0.2, 0.4, 0.8, 1.0)):
    """Cria um material com nós e retorna o material criado."""
    material = bpy.data.materials.new(nome=nome)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = cor
    principled.inputs["Roughness"].default_value = 0.35
    return material


def randomizar_cor(material):
    """Muda a cor Base Color do Principled BSDF para uma cor HSV aleatória."""
    cor = Color()
    cor.hsv = (random.random(), random.uniform(0.65, 1.0),
               random.uniform(0.70, 1.0))

    rgba = (cor.r, cor.g, cor.b, 1.0)
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = rgba
    principled.inputs["Roughness"].default_value = random.uniform(0.25, 0.55)


def randomizar_transformacao(objeto):
    """Aplica rotação, posição e escala aleatórias dentro de limites seguros."""
    objeto.rotation_euler = (
        random.uniform(0.0, 2.0 * math.pi),
        random.uniform(0.0, 2.0 * math.pi),
        random.uniform(0.0, 2.0 * math.pi),
    )

    objeto.location = (
        random.uniform(-0.35, 0.35),
        random.uniform(-0.25, 0.25),
        random.uniform(1.15, 1.55),
    )

    escala = random.uniform(0.80, 1.10)
    objeto.scale = (escala, escala, escala)


def apontar_para(objeto, ponto=(0.0, 0.0, 1.25)):
    """Orienta câmera ou luz para um ponto da cena."""
    direcao = Vector(ponto) - objeto.location
    objeto.rotation_euler = direcao.to_track_quat("-Z", "Y").to_euler()


def criar_luz(nome, localizacao, energia, tamanho=5.0):
    bpy.ops.object.light_add(type="AREA", location=localizacao)
    luz = bpy.context.active_object
    luz.name = nome
    luz.data.energy = energia
    luz.data.shape = "DISK"
    luz.data.size = tamanho
    apontar_para(luz)
    return luz


def configurar_renderizacao():
    cena = bpy.context.scene

    # Blender 4.2+ usa BLENDER_EEVEE_NEXT; versões anteriores usam BLENDER_EEVEE.
    try:
        cena.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        cena.render.engine = "BLENDER_EEVEE"

    cena.render.resolution_x = RESOLUCAO
    cena.render.resolution_y = RESOLUCAO
    cena.render.resolution_percentage = 100
    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_mode = "RGBA"
    cena.render.film_transparent = False

    # Deixa o fundo do mundo levemente azulado/cinza.
    cena.world.color = (0.04, 0.04, 0.04)
    if cena.world.use_nodes:
        fundo = cena.world.node_tree.nodes.get("Background")
        fundo.inputs["Color"].default_value = (0.035, 0.045, 0.06, 1.0)
        fundo.inputs["Strength"].default_value = 0.35


def criar_cenario():
    """Cria chão, fundo curvo, câmera, luzes e as três classes."""
    limpar_cena()
    configurar_renderizacao()

    # Chão
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    chao = bpy.context.active_object
    chao.name = "chao"
    chao.data.materials.append(criar_material("material_chao", (0.16, 0.18, 0.22, 1)))

    # Fundo vertical simples, como um pequeno estúdio.
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 3.2, 5.0),
                                     rotation=(math.radians(90), 0, 0))
    fundo = bpy.context.active_object
    fundo.name = "fundo"
    fundo.data.materials.append(criar_material("material_fundo", (0.12, 0.15, 0.20, 1)))

    # Cubo
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 1.3))
    cubo = bpy.context.active_object
    cubo.name = "cubo"
    cubo.data.materials.append(criar_material("material_cubo"))
    bevel = cubo.modifiers.new(name="bordas_arredondadas", type="BEVEL")
    bevel.width = 0.08
    bevel.segments = 3

    # Esfera
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24,
                                         location=(0, 0, 1.3))
    esfera = bpy.context.active_object
    esfera.name = "esfera"
    esfera.data.materials.append(criar_material("material_esfera"))
    for poligono in esfera.data.polygons:
        poligono.use_smooth = True

    # Cone
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=1.15, radius2=0.0,
                                    depth=2.4, location=(0, 0, 1.3))
    cone = bpy.context.active_object
    cone.name = "cone"
    cone.data.materials.append(criar_material("material_cone"))
    bevel = cone.modifiers.new(name="bordas_arredondadas", type="BEVEL")
    bevel.width = 0.06
    bevel.segments = 3

    # Câmera
    bpy.ops.object.camera_add(location=(6.5, -8.0, 5.2))
    camera = bpy.context.active_object
    camera.name = "camera_dataset"
    camera.data.lens = 52
    apontar_para(camera)
    bpy.context.scene.camera = camera

    # Iluminação de estúdio.
    criar_luz("luz_principal", (4.5, -4.0, 7.0), energia=950, tamanho=5.0)
    criar_luz("luz_preenchimento", (-4.0, -2.0, 4.5), energia=650, tamanho=4.0)
    criar_luz("luz_traseira", (1.0, 4.0, 6.0), energia=800, tamanho=3.5)

    objetos = {nome: bpy.data.objects[nome] for nome in NOMES_DOS_OBJETOS}

    # Começa com apenas o cubo visível.
    for nome, objeto in objetos.items():
        objeto.hide_render = nome != "cubo"
        objeto.hide_viewport = nome != "cubo"

    return objetos


def obter_pasta_saida():
    """Cria a pasta do dataset ao lado do .blend salvo."""
    if bpy.data.filepath:
        pasta_base = Path(bpy.data.filepath).parent
    else:
        pasta_base = Path(bpy.app.tempdir)

    pasta_dataset = pasta_base / NOME_DA_PASTA

    for divisao in IMAGENS_POR_DIVISAO:
        for classe in NOMES_DOS_OBJETOS:
            (pasta_dataset / divisao / classe).mkdir(parents=True, exist_ok=True)

    return pasta_dataset


def gerar_dataset(objetos, pasta_saida):
    """Executa o loop de randomização e renderização."""
    cena = bpy.context.scene
    total_por_classe = sum(IMAGENS_POR_DIVISAO.values())
    total_renderizacoes = total_por_classe * len(NOMES_DOS_OBJETOS)
    numero_global = 0
    inicio = time.time()

    # Esconde todas as classes antes de iniciar.
    for objeto in objetos.values():
        objeto.hide_render = True
        objeto.hide_viewport = True

    for divisao, quantidade in IMAGENS_POR_DIVISAO.items():
        print("\nIniciando divisão: {} | {} imagens".format(
            divisao, quantidade * len(NOMES_DOS_OBJETOS)))

        for nome_classe in NOMES_DOS_OBJETOS:
            objeto = objetos[nome_classe]
            objeto.hide_render = False
            objeto.hide_viewport = False

            print("  Gerando classe: {}".format(nome_classe))

            for indice in range(quantidade):
                randomizar_transformacao(objeto)
                randomizar_cor(objeto.data.materials[0])

                numero_global += 1
                nome_arquivo = "{}_{:04d}.png".format(nome_classe, indice + 1)
                caminho = pasta_saida / divisao / nome_classe / nome_arquivo
                cena.render.filepath = str(caminho)

                bpy.ops.render.render(write_still=True)

                decorrido = time.time() - inicio
                media = decorrido / numero_global
                restante = media * (total_renderizacoes - numero_global)
                print("    [{}/{}] {} | restante: {:.1f} min".format(
                    numero_global, total_renderizacoes, nome_arquivo,
                    restante / 60.0))

            objeto.hide_render = True
            objeto.hide_viewport = True

    duracao = time.time() - inicio
    print("\nDataset concluído!")
    print("Imagens geradas: {}".format(total_renderizacoes))
    print("Tempo total: {:.1f} minutos".format(duracao / 60.0))
    print("Pasta: {}".format(pasta_saida))


# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------

random.seed(SEMENTE_ALEATORIA)

objetos_dataset = criar_cenario()
pasta_dataset = obter_pasta_saida()

# Gera a imagem com os três objetos
gerar_figura_1(objetos_dataset, pasta_dataset)

print("Dataset será salvo em: {}".format(pasta_dataset))
print("Total previsto: {} imagens".format(
    sum(IMAGENS_POR_DIVISAO.values()) * len(NOMES_DOS_OBJETOS)
))

gerar_dataset(objetos_dataset, pasta_dataset)
