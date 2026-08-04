"""
Card 7 - prática autoral: Núcleo de Plasma e Cristais Azuis.
Ana Clara Fortunato de Souza

"""

import bpy
import os
import random
from math import radians, tau
from mathutils import Vector
from bpy.props import FloatProperty, IntProperty


def limpar_cena():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def material_emissivo(nome, cor, forca):
    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    saida = nodes.new('ShaderNodeOutputMaterial')
    emissao = nodes.new('ShaderNodeEmission')
    emissao.inputs['Color'].default_value = cor
    emissao.inputs['Strength'].default_value = forca
    links.new(emissao.outputs['Emission'], saida.inputs['Surface'])
    return mat


def apontar_para(obj, alvo):
    obj.rotation_euler = (Vector(alvo) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def criar_nucleo_plasma(detalhe, distorcao, emissao):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=detalhe, radius=1.55, location=(0, 0, 1.8))
    nucleo = bpy.context.active_object
    nucleo.name = 'Nucleo_Plasma_Azul_Ana'
    bpy.ops.object.shade_smooth()

    ruido_grande = bpy.data.textures.new('Plasma_Ruido_Grande', 'DISTORTED_NOISE')
    ruido_grande.noise_scale = 1.55
    mod_grande = nucleo.modifiers.new('Distorcao_Principal', 'DISPLACE')
    mod_grande.texture = ruido_grande
    mod_grande.strength = distorcao

    ruido_fino = bpy.data.textures.new('Plasma_Ruido_Fino', 'VORONOI')
    ruido_fino.noise_scale = 0.28
    mod_fino = nucleo.modifiers.new('Textura_Fina', 'DISPLACE')
    mod_fino.texture = ruido_fino
    mod_fino.strength = 0.16

    suave = nucleo.modifiers.new('Suavizacao_Final', 'SUBSURF')
    suave.levels = 1
    suave.render_levels = 1

    mat = bpy.data.materials.new('Plasma_Gradiente_Azul')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    saida = nodes.new('ShaderNodeOutputMaterial')
    shader = nodes.new('ShaderNodeEmission')
    rampa = nodes.new('ShaderNodeValToRGB')
    ruido = nodes.new('ShaderNodeTexNoise')
    ruido.inputs['Scale'].default_value = 3.2
    ruido.inputs['Detail'].default_value = 4.0
    rampa.color_ramp.elements[0].color = (0.005, 0.02, 0.35, 1.0)
    rampa.color_ramp.elements[1].color = (0.05, 0.80, 1.0, 1.0)
    shader.inputs['Strength'].default_value = emissao
    links.new(ruido.outputs['Fac'], rampa.inputs['Fac'])
    links.new(rampa.outputs['Color'], shader.inputs['Color'])
    links.new(shader.outputs['Emission'], saida.inputs['Surface'])
    nucleo.data.materials.append(mat)
    nucleo['classe'] = 'nucleo_plasma'
    return nucleo


def criar_cristais(quantidade, emissao):
    cores = [
        (0.01, 0.10, 1.00, 1.0),
        (0.00, 0.42, 1.00, 1.0),
        (0.02, 0.85, 1.00, 1.0),
        (0.18, 0.22, 1.00, 1.0),
    ]
    materiais = [material_emissivo('Cristal_Azul_{:02d}'.format(i + 1), c, emissao * 0.62)
                 for i, c in enumerate(cores)]

    for i in range(quantidade):
        angulo = (i / quantidade) * tau + random.uniform(-0.10, 0.10)
        raio = random.uniform(3.0, 5.2)
        altura = random.uniform(1.4, 3.4)
        bpy.ops.mesh.primitive_cone_add(
            vertices=6,
            radius1=random.uniform(0.35, 0.62),
            radius2=0.0,
            depth=altura,
            location=(raio * __import__('math').cos(angulo),
                      raio * __import__('math').sin(angulo),
                      altura / 2),
        )
        cristal = bpy.context.active_object
        cristal.name = 'Cristal_Azul_{:02d}'.format(i + 1)
        cristal.rotation_euler[0] = radians(random.uniform(-8, 8))
        cristal.rotation_euler[1] = radians(random.uniform(-8, 8))
        cristal.rotation_euler[2] = angulo
        cristal.data.materials.append(random.choice(materiais))
        bevel = cristal.modifiers.new('Bordas_Cristal', 'BEVEL')
        bevel.width = 0.045
        bevel.segments = 2
        cristal['classe'] = 'cristal_azul'
        cristal['indice'] = i + 1


class OBJECT_OT_plasma_cristais_ana(bpy.types.Operator):
    bl_idname = 'object.plasma_cristais_ana'
    bl_label = 'Gerar plasma e cristais azuis - Ana'
    bl_options = {'REGISTER', 'UNDO'}

    quantidade: IntProperty(name='Quantidade de cristais', default=18, min=6, max=40)
    distorcao: FloatProperty(name='Distorção do plasma', default=0.48, min=0.0, max=1.5)
    emissao: FloatProperty(name='Intensidade da emissão', default=4.5, min=0.1, max=15.0)
    semente: IntProperty(name='Semente', default=2026, min=0)

    def execute(self, context):
        random.seed(self.semente)
        limpar_cena()
        cena = context.scene
        cena.render.engine = 'BLENDER_EEVEE'
        cena.render.resolution_x = 800
        cena.render.resolution_y = 800
        cena.render.resolution_percentage = 100
        cena.render.image_settings.file_format = 'PNG'
        cena.world.color = (0.003, 0.006, 0.018)
        if hasattr(cena.eevee, 'use_bloom'):
            cena.eevee.use_bloom = True
            cena.eevee.bloom_intensity = 0.16
            cena.eevee.bloom_radius = 5.5

        criar_nucleo_plasma(4, self.distorcao, self.emissao)
        criar_cristais(self.quantidade, self.emissao)

        bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, -0.04))
        base = context.active_object
        base.name = 'Base_Escura'
        base.data.materials.append(material_emissivo('Base_Azul_Escura', (0.002, 0.006, 0.025, 1), 0.08))

        dados_cam = bpy.data.cameras.new('Camera_Plasma')
        camera = bpy.data.objects.new('Camera_Plasma', dados_cam)
        context.collection.objects.link(camera)
        camera.location = (10.8, -12.5, 9.6)
        dados_cam.lens = 52
        apontar_para(camera, (0, 0, 1.4))
        cena.camera = camera

        dados_luz = bpy.data.lights.new('Luz_Area_Azul', 'AREA')
        dados_luz.energy = 950
        dados_luz.color = (0.08, 0.28, 1.0)
        dados_luz.size = 6
        luz = bpy.data.objects.new('Luz_Area_Azul', dados_luz)
        context.collection.objects.link(luz)
        luz.location = (2, -4, 9)
        apontar_para(luz, (0, 0, 1))
        return {'FINISHED'}


def register():
    bpy.utils.register_class(OBJECT_OT_plasma_cristais_ana)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_plasma_cristais_ana)


if __name__ == '__main__':
    try:
        unregister()
    except Exception:
        pass
    register()
    bpy.ops.object.plasma_cristais_ana()

    pasta = bpy.path.abspath('//')
    if not pasta or pasta == '//':
        pasta = os.path.expanduser('~')
    arquivo_blend = os.path.join(pasta, 'Card7_Pratica_Plasma_Cristais_Azuis_Ana.blend')
    arquivo_render = os.path.join(pasta, 'Card7_Pratica_Plasma_Cristais_Azuis_Ana.png')
    bpy.context.scene.render.filepath = arquivo_render
    bpy.ops.wm.save_as_mainfile(filepath=arquivo_blend)
    bpy.ops.render.render(write_still=True)
    print('Arquivos salvos em:', pasta)
