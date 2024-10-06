extends Label3D


func _ready() -> void:
	pass # Replace with function body.


func _show():
	self.text = "0-10 cm soil moisture content,\nFLDAS Noah 0.1 x 0.1 degree"
	
func _hide():
	self.text = ""
# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass
