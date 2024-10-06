extends Label3D

var file = "res://croppa/ch10.json"
var json_as_text = FileAccess.get_file_as_string(file).left(5)
var json_as_text_t = json_as_text
var arrow = ""
# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass # Replace with function body.

func _show():
	if json_as_text.left(1) != "-":
		json_as_text_t = " + " + json_as_text
		arrow = " ↑ "
		modulate = Color.GREEN_YELLOW
	else:
		modulate = Color.ORANGE_RED
		arrow = " ↓ "
	self.text = arrow + "5Y change (median): %s " % [json_as_text_t] + " (%)"
	
func _hide():
	self.text = ""
# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass
