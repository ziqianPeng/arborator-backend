from datetime import datetime
from typing import Dict, List, NewType, Union
import json
import base64

from sqlalchemy.sql.sqltypes import Date, DateTime

from app import db
from flask import abort, current_app
from flask_login import current_user

from ..user.model import User
from .interface import ProjectExtendedInterface, ProjectInterface
from .model import Project, ProjectAccess, ProjectFeature, ProjectMetaFeature, DefaultUserTrees, LastAccess
from ..samples.model import SampleRole


class ProjectService:
    @staticmethod
    def get_all() -> List[Project]:
        return Project.query.all()

    @staticmethod
    def create(new_attrs: ProjectInterface) -> Project:
        new_project = Project(**new_attrs)
        db.session.add(new_project)
        db.session.commit()
        return new_project

    @staticmethod
    def get_by_name(project_name: str) -> Project:
        return Project.query.filter(Project.project_name == project_name).first()

    @staticmethod
    def update(project: Project, changes) -> Project:
        project.update(changes)
        db.session.commit()
        return project

    @staticmethod
    def delete_by_name(project_name: str) -> str:
        project = Project.query.filter(
            Project.project_name == project_name).first()
        if not project:
            return ""
        db.session.delete(project)
        db.session.commit()
        return project_name

    @staticmethod
    def change_image(project_name, value):
        """ set a project image (path) and return the new project  """
        project = Project.query.filter(
            Project.project_name == project_name).first()
        project.image = value
        db.session.commit()
        print('change_image done')
        return project

    @staticmethod
    def check_if_project_exist(project: Project) -> None:
        if not project:
            message = "There was no such project stored on arborator backend"
            abort(404, {"message": message})

    # @staticmethod
    # def get_settings_infos(project_name, current_user):
    #     """ get project informations without any samples """
    #     project = Project.query.filter(Project.project_name == project_name).first()
    #     if not current_user.is_authenticated:  # TODO : handle anonymous user
    #         roles = []
    #     else:
    #         roles = set(SampleRole.query.filter_by(project_id = project.id, user_id = current_user.id).all())
    #     # if not roles and project.is_private: return 403 # removed for now -> the check is done in view and for each actions
    #     admins = [a.user_id for a in ProjectAccess.query.filter_by(project_id=project.id, access_level=2).all()]
    #     guests = [g.user_id for g in ProjectAccess.query.filter_by(project_id=project.id, access_level=1).all()]

    #     # config from arborator
    #     features = ProjectFeature.query.filter_by(project_id=project.id).all()
    #     shown_features =  [f.value for f in features] if features else []

    #     mfs = ProjectMetaFeature.query.filter_by(project_id=project.id)
    #     shown_metafeatures = [mf.value for mf in mfs] if mfs else []

    #     # config from grew
    #     reply = grew_request("getProjectConfig", current_app, data={"project_id": project_name})
    #     if reply["status"] != "OK":
    #         abort(400)
    #     annotationFeatures = reply["data"]
    #     if annotationFeatures is None:
    #         print("This project does not have a configuration stored on grew")

    #     config = {
    #         "shownfeatures": shown_features,
    #         "shownmeta": shown_metafeatures,
    #         "annotationFeatures": annotationFeatures,
    #     }

    #     # cats = [c.value for c in project_dao.find_project_cats(project.id)]
    #     # stocks = project_dao.find_project_stocks(project.id)
    #     # labels = [ {'id':s.id,'labels':[ {"id":l.id, "stock_id":l.stock_id , "value":l.value} for l in project_dao.find_stock_labels(s.id) ]}  for s in stocks ]
    #     defaultUserTrees = [
    #         u.as_json() for u in DefaultUserTrees.query.filter_by(project_id=project.id).all()
    #     ]
    #     # if project.image != None:
    #     #     image = str(base64.b64encode(project.image))
    #     # else:
    #     #     image = ""
    #     settings_info = {
    #         # "name": project.project_name,
    #         # "visibility": project.visibility,
    #         # "description": project.description,
    #         # "image": image,
    #         "config": config,
    #         # "admins": admins,
    #         # "guests": guests,
    #         # "show_all_trees": project.show_all_trees,
    #         # "exercise_mode": project.exercise_mode,
    #         # "default_user_trees": defaultUserTrees,
    #     }
    #     return settings_info


class ProjectAccessService:
    @staticmethod
    def create(new_attrs) -> ProjectAccess:
        new_project_access = ProjectAccess(**new_attrs)
        db.session.add(new_project_access)
        db.session.commit()
        return new_project_access

    @staticmethod
    def update(project_access: ProjectAccess, changes):
        project_access.update(changes)
        db.session.commit()
        return project_access

    @staticmethod
    def delete(user_id: str, project_id: int):
        project_access_list = ProjectAccess.query.filter_by(
            user_id=user_id, project_id=project_id
        ).all()
        if not project_access_list:
            return []
        for project_access in project_access_list:
            db.session.delete(project_access)
            db.session.commit()
        return [(project_id, user_id)]

    # TODO : Rename this as `get_by_username` because we are not fetching the user_id
    # ... but the username
    @staticmethod
    def get_by_user_id(user_id: str, project_id: str) -> ProjectAccess:
        return ProjectAccess.query.filter_by(
            project_id=project_id, user_id=user_id
        ).first()

    @staticmethod
    def get_admins(project_id: str) -> List[str]:
        project_access_list: List[ProjectAccess] = ProjectAccess.query.filter_by(
            project_id=project_id, access_level=2
        )
        if project_access_list:
            return [project_access.user_id for project_access in project_access_list]
        else:
            return []

    @staticmethod
    def get_guests(project_id: str) -> List[str]:
        project_access_list: List[ProjectAccess] = ProjectAccess.query.filter_by(
            project_id=project_id, access_level=1
        )
        if project_access_list:
            return [project_access.user_id for project_access in project_access_list]
        else:
            return []

    @staticmethod
    def get_all(project_id: str) -> List[str]:
        '''optimized version dedicated to homepage. reduces the database calls but makes the code less pretty'''
        project_access_list: List[ProjectAccess] = ProjectAccess.query.filter_by(project_id=project_id).all()
        admins, guests = [], []
        push_admin, push_guest = admins.append, guests.append
        for project_access in project_access_list: 
            if project_access.access_level==1: push_guest(project_access.user_id)
            elif project_access.access_level==2: push_admin(project_access.user_id)
        return admins, guests

    @staticmethod
    def get_users_role(project_id: str) -> Dict[str, List[str]]:
        admins = ProjectAccessService.get_admins(project_id)
        guests = ProjectAccessService.get_guests(project_id)
        return {
            "admins": admins,
            "guests": guests,
        }

    @staticmethod
    def require_access_level(project_id, required_access_level) -> None:
        access_level = 0
        if current_user.is_authenticated:
            if current_user.super_admin:
                pass

            else:
                access_level = ProjectAccessService.get_by_user_id(
                    current_user.id, project_id
                ).access_level.code

        if access_level >= required_access_level:
            return
        else:
            abort(403)


class ProjectFeatureService:
    @staticmethod
    def create(new_attrs) -> ProjectFeature:
        new_project_access = ProjectFeature(**new_attrs)
        db.session.add(new_project_access)
        db.session.commit()
        return new_project_access

    @staticmethod
    def get_by_project_id(project_id: str) -> List[str]:
        features = ProjectFeature.query.filter_by(project_id=project_id).all()
        if features:
            return [f.value for f in features]
        else:
            return []

    @staticmethod
    def delete_by_project_id(project_id: str) -> str:
        """TODO : Delete all the project features at once. This is a weird way of doing, but it's because we have a table specificaly
        ...dedicated for linking project shown features and project. Maybe a simple textfield in the project settings would do the job"""
        features = ProjectFeature.query.filter_by(project_id=project_id).all()
        for feature in features:
            db.session.delete(feature)
            db.session.commit()
        return project_id


class ProjectMetaFeatureService:
    @staticmethod
    def create(new_attrs) -> ProjectMetaFeature:
        new_project_access = ProjectMetaFeature(**new_attrs)
        db.session.add(new_project_access)
        db.session.commit()
        return new_project_access

    @staticmethod
    def get_by_project_id(project_id: str) -> List[str]:
        meta_features = ProjectMetaFeature.query.filter_by(
            project_id=project_id).all()

        if meta_features:
            return [meta_feature.value for meta_feature in meta_features]
        else:
            return []

    @staticmethod
    def delete_by_project_id(project_id: str) -> str:
        """Delete all the project features at once. This is a weird way of doing, but it's because we have a table specificaly
        ...dedicated for linking project shown features and project. Maybe a simple textfield in the project settings would do the job"""
        features = ProjectMetaFeature.query.filter_by(
            project_id=project_id).all()
        for feature in features:
            db.session.delete(feature)
            db.session.commit()
        return project_id


class LastAccessService:
    @staticmethod
    def get_last_access_time_per_project(project_name, access_type="any"):
        """return the last access for a project
        project_id: string, id of the project
        access_type: "write" ,"read", "any", "any+write"
        """
        if access_type not in ["any", "read", "write", "any+write"]:
            raise f"ERROR by the coder in LastAccessService, access_type not in 'any' 'read' 'write'"
        
        last_accesss: List[LastAccess] = LastAccess.query.join(Project).filter(Project.project_name == project_name).all()
        
        # less "pretty" version but with decreased complexity
        if access_type == "any+write":
            last_read, last_write = 0, 0
            for last_access in last_accesss:
                if last_access.last_read or 0 > last_read:   last_read = last_access.last_read
                if last_access.last_write or 0 > last_write: last_write = last_access.last_write
            return max(last_read, last_write), last_write
        elif access_type == "any":
            last_read = 0
            last_write = 0
            for last_access in last_accesss:
                if last_access.last_read or 0 > last_read:   last_read = last_access.last_read
                if last_access.last_write or 0 > last_write: last_write = last_access.last_write
            return max(last_read, last_write)
        elif access_type == "write":
            last_write = 0
            for last_access in last_accesss:
                if last_access.last_write or 0 > last_write: last_write = last_access.last_write
            return last_write
        elif access_type == "read":
            last_read = 0
            for last_access in last_accesss:
                if last_access.last_read or 0 > last_read:   last_read = last_access.last_read
            return last_read


    @staticmethod
    def get_last_access_time_per_user(username, access_type="any"):
        if access_type not in ["any", "read", "write"]:
            raise f"ERROR by the coder in LastAccessService, access_type not in 'any' 'read' 'write'"

        last_accesss: List[LastAccess] = LastAccess.join(User).query.filter(User.username == username).all()

        last_read = 0
        last_write = 0
        for last_access in last_accesss:
            if last_access.last_read or 0 > last_read:
                last_read = last_access.last_read
            if last_access.last_write or 0 > last_write:
                last_write = last_access.last_write
        
        if access_type == "any":
            return max(last_read, last_write)
        elif access_type == "write":
            return last_write
        elif access_type == "read":
            return last_read

    @staticmethod
    def get_last_access_time_per_user_and_project(username, project_name, access_type="any"):
        if access_type not in ["any", "read", "write"]:
            raise f"ERROR by the coder in LastAccessService, access_type not in 'any' 'read' 'write'"

        last_accesss: LastAccess = LastAccess.join(User).query.filter(User.username == username).join(Project).query.filter(Project.project_name == project_name).first()
        # TODO : is the datetime in the database a integer ? Or a special datetime object ? Be careful for the comparaison
        last_read = 0
        last_write = 0


        if last_accesss:
            last_read = last_accesss.last_read
            last_write = last_accesss.last_write

        if access_type == "any":
            return max(last_read, last_write)
        elif access_type == "write":
            return last_write
        elif access_type == "read":
            return last_read
        

    @staticmethod
    def update_last_access_per_user_and_project(user_id, project_name, access_type):
        if access_type not in ["read", "write"]:
            raise f"ERROR by the coder in LastAccessService, access_type not in 'read' 'write'"

        project: Project = Project.query.filter(Project.project_name == project_name).first()
        if not user_id and not project:
            print("user or project missing")
            return None

        last_accesss: LastAccess = LastAccess.query.filter(LastAccess.user_id == user_id).filter(LastAccess.project_id == project.id).first()
        
        time_now_ts = datetime.now().timestamp()

        if not last_accesss:
            new_data = {
                "project_id": project.id,
                "user_id": user_id,
                "last_write": None if (access_type == "read") else time_now_ts,
                "last_read": None if (access_type == "write") else time_now_ts,
            }
            new_last_access = LastAccess(**new_data)
            db.session.add(new_last_access)
            db.session.commit()

        else:
            if access_type == "read":
                last_accesss.last_read = time_now_ts
            else:
                last_accesss.last_write = time_now_ts
            db.session.commit()
            