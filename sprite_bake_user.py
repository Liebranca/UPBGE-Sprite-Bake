import sprite_bake, importlib

sheet_name = "maledef_attack" #unique id for sprite object
sheet_size = [ 6, 5 ] #[ tiles on x, tiles on y ]

importlib.reload(sprite_bake)
sprite_bake.run(sheet_name, *sheet_size)