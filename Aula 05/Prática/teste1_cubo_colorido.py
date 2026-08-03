# STrocando a cor de um cubo
# Conceito: criar material, ativar nós e mudar a cor base

import bpy

# Cria o cubo
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cubo = bpy.context.active_object
cubo.name = "CuboColorido"

# Cria um material azul
mat = bpy.data.materials.new(name="MeuAzul")
mat.use_nodes = True

# Pega o nó Principled BSDF e muda a cor base para azul
principled = mat.node_tree.nodes.get("Principled BSDF")
principled.inputs["Base Color"].default_value = (0.1, 0.3, 0.8, 1.0)  # R, G, B, A
principled.inputs["Roughness"].default_value = 0.4

# Aplica o material ao cubo
cubo.data.materials.append(mat)

print("Cubo azul criado")