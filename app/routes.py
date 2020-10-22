def register_routes(api, app, root="api"):
    from app.user import register_routes as attach_user
    from app.projects import register_routes as attach_projects
    from app.samples import register_routes as attach_samples
    from app.trees import register_routes as attach_trees
    from app.lexicon import register_routes as attach_lexicon
    from app.grew import register_routes as attach_grew

    # Add routes
    attach_user(api, app, root)
    attach_projects(api, app, root)
    attach_samples(api, app, root)
    attach_trees(api, app, root)
    attach_lexicon(api, app, root)
    attach_grew(api, app, root)
