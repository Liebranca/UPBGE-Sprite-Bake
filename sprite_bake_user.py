import sprite_bake

sheet_name = "Sprite" #unique id for sprite object and generated image
sheet_size = [ 2, 2 ] #[ tiles on x, tiles on y ]

#sprite sheet will be saved to render output filepath
sprite_bake.run(sheet_name, *sheet_size)
