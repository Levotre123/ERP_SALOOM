def post_init_hook(env):
    env["res.lang"]._ma_ensure_recommended_languages()
