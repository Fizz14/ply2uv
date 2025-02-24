import bpy
import struct
import os

bl_info = {
    "name": "ply2uv importer",
    "blender": (2, 80, 0),
    "category": "Import-Export",
    "version": (1, 0, 0),
    "location": "File > Import",
    "description": "Import ply mesh with two UV coordinates",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "author": "JM"
}

def read_some_data(filepath):
    with open(filepath, "rb") as f:
        header = []
        while True:
            line = f.readline().decode('ascii').strip()
            if line == "end_header":
                break
            header.append(line)

        element_vertex = 0
        element_face = 0
        for line in header:
            if line.startswith("element vertex"):
                element_vertex = int(line.split()[-1])
            elif line.startswith("element face"):
                element_face = int(line.split()[-1])

        vertices = []
        uvs1 = []
        uvs2 = []
        for _ in range(element_vertex):
            data = struct.unpack('fff ff ff', f.read(28))  # Correct buffer size for 3 + 2 + 2 floats
            vertices.append(data[:3])
            uvs1.append(data[3:5])
            uvs2.append(data[5:])

        faces = []
        for _ in range(element_face):
            _ = struct.unpack('B', f.read(1))[0]
            face = struct.unpack('III', f.read(12))
            faces.append(face)

    return vertices, uvs1, uvs2, faces

def create_mesh(context, name, vertices, uvs1, uvs2, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    if not mesh.uv_layers:
        mesh.uv_layers.new(name='UVMap')
        mesh.uv_layers.new(name='UVMap.001')

    for i, loop in enumerate(mesh.loops):
        loop_uv1 = mesh.uv_layers[0].data[i].uv
        loop_uv2 = mesh.uv_layers[1].data[i].uv
        loop_uv1[0], loop_uv1[1] = uvs1[loop.vertex_index]
        loop_uv2[0], loop_uv2[1] = uvs2[loop.vertex_index]

    obj = bpy.data.objects.new(name, mesh)
    context.collection.objects.link(obj)

    return {'FINISHED'}

from bpy_extras.io_utils import ImportHelper

class ImportSomeData(bpy.types.Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_ply2uv.data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import ply2uv"

    filter_glob: bpy.props.StringProperty(
        default="*.ply",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    filename_ext = ".ply"

    def execute(self, context):
        vertices, uvs1, uvs2, faces = read_some_data(self.filepath)
        return create_mesh(context, os.path.basename(self.filepath), vertices, uvs1, uvs2, faces)

def menu_func_import(self, context):
    self.layout.operator(ImportSomeData.bl_idname, text="ply2uv")

def register():
    bpy.utils.register_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_ply2uv.data('INVOKE_DEFAULT')
