import bpy
import struct
import os

bl_info = {
    "name": "ply2uv exporter",
    "blender": (2, 80, 0),
    "category": "Import-Export",
    "version": (1, 0, 0),
    "location": "File > Export",
    "description": "Export ply mesh with up to two UV coordinates and optional vertex colors",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "author": "JM"
}

def jprint(filepath, message, enable_logging):
    if enable_logging:
        with open(filepath, 'a') as f:
            f.write(message + '\n')

def write_some_data(context, filepath, use_logging):
    debug_log = os.path.join(os.path.dirname(filepath), "debug_log.txt")
    
    # Clear the debug log file if logging is enabled
    if use_logging:
        with open(debug_log, 'w') as f:
            f.write("")  # Clears the file content
    
    jprint(debug_log, "running write_some_data...", use_logging)

    obj = bpy.context.active_object
    if obj is None or obj.type != 'MESH' or not obj.select_get():
        jprint(debug_log, "Error: No active and selected mesh object", use_logging)
        return {'CANCELLED'}
    
    mesh = obj.data
    mesh.calc_loop_triangles()

    vertices = []
    uvs1 = []
    uvs2 = []
    colors = []

    num_uv_layers = len(mesh.uv_layers)
    has_colors = len(mesh.vertex_colors) > 0
    if has_colors:
        color_layer = mesh.vertex_colors.active.data

    for vert in mesh.vertices:
        vertices.append((vert.co.x, vert.co.y, vert.co.z))

    for vertex in mesh.vertices:
        # Find all the loops corresponding to the current vertex
        loops = [loop for loop in mesh.loops if loop.vertex_index == vertex.index]

        # Collect the UV coordinates for the first UV layer
        if num_uv_layers > 0:
            uv1_coords = [mesh.uv_layers[0].data[loop.index].uv for loop in loops]
            uvs1.append(uv1_coords[0])  # Take the first UV coordinate for the vertex
        else:
            uvs1.append((0.0, 0.0))

        # Check if there are multiple UV layers
        if num_uv_layers > 1:
            uv2_coords = [mesh.uv_layers[1].data[loop.index].uv for loop in loops]
            jprint(debug_log, f"Second UV Layer - Vertex {vertex.index}: {uv2_coords}", use_logging)
            uvs2.append(uv2_coords[0])  # Take the first UV coordinate for the vertex
        else:
            jprint(debug_log, "Couldn't find 2nd UVs", use_logging)
            uvs2.append((0.0, 0.0))

        if has_colors:
            color_coords = [color_layer[loop.index].color for loop in loops]
            colors.append(color_coords[0])  # Take the first color for the vertex
        else:
            colors.append((1.0, 1.0, 1.0, 1.0))

    faces = []
    for tri in mesh.loop_triangles:
        face = [mesh.loops[loop_index].vertex_index for loop_index in tri.loops]
        faces.append(face)

    jprint(debug_log, f"Writing data to {filepath}", use_logging)
    
    with open(filepath, "wb") as f:
        f.write(b"ply\n")
        f.write(b"format binary_little_endian 1.0\n")
        f.write(f"element vertex {len(vertices)}\n".encode())
        f.write(b"property float x\n")
        f.write(b"property float y\n")
        f.write(b"property float z\n")
        if num_uv_layers > 0:
            f.write(b"property float s\n")
            f.write(b"property float t\n")
        if num_uv_layers > 1:
            f.write(b"property float u\n")
            f.write(b"property float v\n")
        if has_colors:
            f.write(b"property uchar red\n")
            f.write(b"property uchar green\n")
            f.write(b"property uchar blue\n")
        f.write(f"element face {len(faces)}\n".encode())
        f.write(b"property list uchar int vertex_indices\n")
        f.write(b"end_header\n")

        for i, vert in enumerate(vertices):
            uv1 = uvs1[i] if num_uv_layers > 0 else (0.0, 0.0)
            uv2 = uvs2[i] if num_uv_layers > 1 else (0.0, 0.0)
            color = colors[i] if has_colors else (1.0, 1.0, 1.0, 1.0)
            jprint(debug_log, f"v: {vert[0]}, {vert[1]}, {vert[2]} : {uv1[0]} {uv1[1]} : {uv2[0]} {uv2[1]} : {color[0]} {color[1]} {color[2]} {color[3]}", use_logging)
            f.write(struct.pack('fff', vert[0], vert[1], vert[2]))
            if num_uv_layers > 0:
                f.write(struct.pack('ff', uv1[0], uv1[1]))
            if num_uv_layers > 1:
                f.write(struct.pack('ff', uv2[0], uv2[1]))
            if has_colors:
                jprint(debug_log, "Writing vertex color", use_logging)
                jprint(debug_log, str(color[0]), use_logging)
                jprint(debug_log, str(int(color[0])*255), use_logging)
                r = int(color[0] * 255)
                g = int(color[1] * 255)
                b = int(color[2] * 255)
                #f.write(struct.pack('BBB', int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)))
                f.write(struct.pack('BBB', r, g, b))
                
        for face in faces:
            jprint(debug_log, "Face len is " + str(len(face)), use_logging)
            jprint(debug_log, f"{face[0]} {face[1]} {face[2]}", use_logging)
            f.write(struct.pack('B', 3))
            f.write(struct.pack('I', face[0]))
            f.write(struct.pack('I', face[1]))
            f.write(struct.pack('I', face[2]))

    jprint(debug_log, f"Binary PLY file saved to {filepath}", use_logging)

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

    use_logging: BoolProperty(
        name="Enable Logging",
        description="Enable debug logging to a file",
        default=False,
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
        return write_some_data(context, self.filepath, self.use_logging)

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
    bpy.ops.export_ply2uv.data('INVOKE_DEFAULT')
