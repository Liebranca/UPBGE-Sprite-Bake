import sprite_bake

sheet_name = "sprite_sheet" #unique id for sprite object
sheet_size = [ 4, 2 ] #[ tiles on x, tiles on y ]

sprite_bake.run(sheet_name, *sheet_size)