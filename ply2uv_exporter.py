import bpy
import struct
import os

bl_info = {
    "name": "ply2uv exporter",
    "blender": (2, 80, 0),
    "category": "Import-Export",
    "version": (1, 0, 0),
    "location": "File > Export",
    "description": "Export ply mesh with two UV coordinates",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "author": "JM"
    }

def jprint(filepath, message):
    with open(filepath, 'a') as f:
        f.write(message + '\n')

def write_some_data(context, filepath, use_some_setting):
    debug_log = os.path.join(os.path.dirname(filepath), "debug_log.txt")
    
    # Clear the debug log file
    with open(debug_log, 'w') as f:
        f.write("")  # Clears the file content
    
    jprint(debug_log, "running write_some_data...")

    obj = bpy.context.active_object
    mesh = obj.data
    mesh.calc_loop_triangles()

    vertices = []
    uvs1 = []
    uvs2 = []

    num_uv_layers = len(mesh.uv_layers)
    if num_uv_layers < 1:
        jprint(debug_log, "Error: Mesh needs at least one UV layer")
        return {'CANCELLED'}

    for i, vert in enumerate(mesh.vertices):
        vertices.append((vert.co.x, vert.co.y, vert.co.z))

    for vertex in mesh.vertices:
        # Find all the loops corresponding to the current vertex
        loops = [loop for loop in mesh.loops if loop.vertex_index == vertex.index]

        # Collect the UV coordinates for the first UV layer
        uv1_coords = [mesh.uv_layers[0].data[loop.index].uv for loop in loops]
        uvs1.append(uv1_coords)

        # Check if there are multiple UV layers
        if num_uv_layers > 1:
            # Collect the UV coordinates for the second UV layer
            uv2_coords = [mesh.uv_layers[1].data[loop.index].uv for loop in loops]
            jprint(debug_log, f"Second UV Layer - Vertex {vertex.index}: {uv2_coords}")
            uvs2.append(uv2_coords)
        else:
            jprint("Couldn't find 2nd UVs")
            uvs2.append([(0.0, 0.0)])
                

    faces = []
    for tri in mesh.loop_triangles:
        face = []
        for loop_index in tri.loops:
            face.append(mesh.loops[loop_index].vertex_index)
        faces.append(face)

    jprint(debug_log, f"Writing data to {filepath}")
    
    with open(filepath, "wb") as f:
        f.write(b"ply\n")
        f.write(b"format binary_little_endian 1.0\n")
        f.write(f"element vertex {len(vertices)}\n".encode())
        f.write(b"property float x\n")
        f.write(b"property float y\n")
        f.write(b"property float z\n")
        f.write(b"property float s\n")
        f.write(b"property float t\n")
        f.write(b"property float u\n")
        f.write(b"property float v\n")
        f.write(f"element face {len(faces)}\n".encode())
        f.write(b"property list uchar int vertex_indices\n")
        f.write(b"end_header\n")

        for i, vert in enumerate(vertices):
            uv1 = uvs1[i][0]  # Extract the first UV coordinate for the vertex
            uv2 = uvs2[i][0]  # Extract the first UV coordinate for the vertex
            jprint(debug_log, f"v: {vert[0]}, {vert[1]}, {vert[2]} : {uv1.x} {uv1.y} : {uv2.x} {uv2.y}")
            f.write(struct.pack('fff', vert[0], vert[1], vert[2]))
            f.write(struct.pack('ff', uv1.x, uv1.y))
            f.write(struct.pack('ff', uv2.x, uv2.y))

        for face in faces:
            jprint(debug_log, "Face len is " + str(len(face)))
            jprint(debug_log, f"{face[0]} {face[1]} {face[2]}")
            f.write(struct.pack('B', 3))
            f.write(struct.pack('I', face[0]))
            f.write(struct.pack('I', face[1]))
            f.write(struct.pack('I', face[2]))

    jprint(debug_log, f"Binary PLY file saved to {filepath}")

    return {'FINISHED'}

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ExportSomeData(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "export_ply2uv.data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export ply2uv"

    # ExportHelper mix-in class uses this.
    filename_ext = ".ply"

    filter_glob: StringProperty(
        default="*.ply",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )

    type: EnumProperty(
        name="Example Enum",
        description="Choose between two items",
        items=(
            ('OPT_A', "First Option", "Description one"),
            ('OPT_B', "Second Option", "Description two"),
        ),
        default='OPT_A',
    )

    def execute(self, context):
        return write_some_data(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportSomeData.bl_idname, text="ply2uv")


# Register and add to the "file selector" menu (required to use F3 search "Text Export Operator" for quick access).
def register():
    bpy.utils.register_class(ExportSomeData)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportSomeData)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_test.some_data('INVOKE_DEFAULT')
