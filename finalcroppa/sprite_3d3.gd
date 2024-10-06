extends Sprite3D

signal input_event(camera: Node, event: InputEvent, position: Vector3, normal: Vector3)
signal mouse_entered()
signal mouse_exited()

var mouse_over := false
var image : Image

@onready var collision_shape := $Area3D/CollisionShape3D

var _mouse_input_received := false

func load_texture():
	var new_texture = ResourceLoader.load("res://croppa/SM2024-10cm.tif.png")
	self.texture = new_texture

func _ready():
	load_texture()
	modulate.a = 0.2
	# Duplicate collision shape so it's unique

	collision_shape.shape = collision_shape.shape.duplicate()

	# Update image and collision shape
	
	_on_texture_changed()

	# Connect camera signal

	var camera = get_viewport().get_camera_3d()

	if camera.has_signal("mouse_ray_processed"):
		camera.mouse_ray_processed.connect(_on_3d_mouse_ray_processed)


func _on_3d_mouse_ray_processed() -> void:

	# Received Input

	if _mouse_input_received:

		# Mouse Entered Case

		if !mouse_over:
			mouse_over = true
			mouse_entered.emit()
	
	# Mouse Exited Case

	elif mouse_over:
		mouse_over = false
		mouse_exited.emit()
	
	_mouse_input_received = false


func _on_texture_changed() -> void:
	self.texture = ResourceLoader.load("res://croppa/SM2024-10cm.tif.png")
	# We call this only when the texture is changed to save on performance
	
	image = texture.get_image()

	# Call this to allow get_pixel later (thanks Godot 4.2)

	if image.is_compressed():
		image.decompress()

	# Update CollisionShape parameters

	collision_shape.shape.size.x = texture.get_width() * pixel_size
	collision_shape.shape.size.y = texture.get_height() * pixel_size
	


func _on_mouse_entered():
	modulate.a = 0.8
	$Label3D._show()
	$Label3D2._show()

func _on_mouse_exited():
	modulate.a = 0.1
	$Label3D._hide()
	$Label3D2._hide()
# Takes the variables of the standard input_event signal

func try_mouse_input(camera: Node, event: InputEvent, input_position: Vector3, normal: Vector3) -> bool:
	if is_pixel_opaque(input_position):
		_mouse_input_received = true
		input_event.emit(camera, event, input_position, normal)
		return true
	else:
		return false


func is_pixel_opaque(input_position: Vector3) -> bool:

	# Convert input position to Image local position

	var pixel_position = (input_position - global_position) / (pixel_size * scale)

	var texture_local_x = pixel_position.x + (texture.get_width() / 2.0)
	var texture_local_y = texture.get_height() - (pixel_position.y + texture.get_height() / 2.0)  # Invert the Y position because 2D Y coordinates are inverted

	# Return true if Alpha of given pixel is greater than 0 (aka opaque)

	return image.get_pixel(texture_local_x, texture_local_y).a > 0.0
