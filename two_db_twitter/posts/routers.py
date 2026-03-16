class PostRouter:

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'posts':
            if model.__name__ == 'Profile':
                return 'default'
            return 'postgres'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'posts':
            if model.__name__ == 'Profile':
                return 'default'
            return 'postgres'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._state.db == 'postgres' and obj2._state.db == 'postgres':
            return True
        if obj1._state.db == 'default' and obj2._state.db == 'default':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'posts':
            if model_name == 'profile':
                return db == 'default'
            return db == 'postgres'
        return db == 'default'
