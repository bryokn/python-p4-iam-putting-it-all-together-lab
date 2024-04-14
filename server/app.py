#!/usr/bin/env python3

from flask import request, session, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        user = User(
            username=data['username'],
            bio=data['bio'],
            image_url=data['image_url']
        )
        user.password_hash = data['password']
        try:
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }, 201
        except IntegrityError:
            db.session.rollback()
            return {'error': 'Username already exists'}, 422

class CheckSession(Resource):
    def get(self):
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            return jsonify({
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }), 200
        else:
            return {'error': 'Not logged in'}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        if user and user.verify_password(data['password']):
            session['user_id'] = user.id
            return jsonify({
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            })
        else:
            return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        if 'user_id' in session:
            del session['user_id']
            return '', 204
        else:
            return {'error': 'Not logged in'}, 401

class RecipeIndex(Resource):
    def get(self):
        if 'user_id' in session:
            recipes = Recipe.query.filter_by(user_id=session['user_id']).all()
            return jsonify([recipe.to_dict(only=('title', 'instructions', 'minutes_to_complete'), include_relations={'user': ('id', 'username', 'image_url', 'bio')}) for recipe in recipes]), 200
        else:
            return {'error': 'Not logged in'}, 401

    def post(self):
        if 'user_id' in session:
            data = request.get_json()
            recipe = Recipe(
                title=data['title'],
                instructions=data['instructions'],
                minutes_to_complete=data['minutes_to_complete'],
                user_id=session['user_id']
            )
            try:
                db.session.add(recipe)
                db.session.commit()
                return jsonify(recipe.to_dict(only=('title', 'instructions', 'minutes_to_complete'), include_relations={'user': ('id', 'username', 'image_url', 'bio')})), 201
            except IntegrityError:
                db.session.rollback()
                return {'errors': {'title': ['Title is required'], 'instructions': ['Instructions must be at least 50 characters']}}, 422
        else:
            return {'error': 'Not logged in'}, 401

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)