"""
Enunciado:
Desarrolla una API REST utilizando Flask que permita realizar operaciones básicas sobre una biblioteca
con dos modelos relacionados: Autores y Libros.
La API debe exponer los siguientes endpoints:

Autores:
1. `GET /authors`: Devuelve la lista completa de autores.
2. `POST /authors`: Agrega un nuevo autor. El cuerpo de la solicitud debe incluir un JSON con el campo "name".
3. `GET /authors/<author_id>`: Obtiene los detalles de un autor específico y su lista de libros.

Libros:
1. `GET /books`: Devuelve la lista completa de libros.
2. `POST /books`: Agrega un nuevo libro. El cuerpo de la solicitud debe incluir JSON con campos "title", "author_id", y "year" (opcional).
3. `DELETE /books/<book_id>`: Elimina un libro específico por su ID.
4. `PUT /books/<book_id>`: Actualiza la información de un libro existente. El cuerpo puede incluir "title" y/o "year".

Esta versión utiliza Flask-SQLAlchemy como ORM para persistir los datos en una base de datos SQLite.
"""

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Define aquí tus modelos
# Usa los mismos modelos que en el ejercicio anterior: Author y Book

class Author(db.Model):
    """
    Modelo de autor usando SQLAlchemy ORM
    Debe tener: id, name y una relación con los libros
    """
    # Define la tabla 'authors' con:
    # - __tablename__ para especificar el nombre de la tabla
    # - id: clave primaria autoincremental
    # - name: nombre del autor (obligatorio)
    # - Una relación con los libros usando db.relationship
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)

    books = db.relationship(
        "Book",
        back_populates="author",
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convierte el autor a un diccionario para la respuesta JSON"""
        # Implementa este método para devolver id y name
        # No incluyas la lista de libros para evitar recursión infinita
        return {
            "id": self.id,
            "name": self.name
        }


class Book(db.Model):
    """
    Modelo de libro usando SQLAlchemy ORM
    Debe tener: id, title, year (opcional), author_id y relación con el autor
    """
    # Define la tabla 'books' con:
    # - __tablename__ para especificar el nombre de la tabla
    # - id: clave primaria autoincremental
    # - title: título del libro (obligatorio)
    # - year: año de publicación (opcional)
    # - author_id: clave foránea que relaciona con la tabla 'authors'
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=True)

    author_id = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False)

    author = db.relationship("Author", back_populates="books")

    def to_dict(self):
        """Convierte el libro a un diccionario para la respuesta JSON"""
        # Implementa este método para devolver id, title, year y author_id
        return {
            "id": self.id,
            "title": self.title,
            "year": self.year,
            "author_id": self.author_id
        }


def create_app():
    """
    Crea y configura la aplicación Flask con SQLAlchemy
    """
    app = Flask(__name__)
    
    # Configuración de la base de datos SQLite en memoria
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializa la base de datos con la aplicación
    db.init_app(app)
    
    # Crea todas las tablas en la base de datos
    with app.app_context():
        db.create_all()
    
    # Endpoints de Autores
    @app.route('/authors', methods=['GET'])
    def get_authors():
        """
        Devuelve la lista completa de autores
        """
        # Implementa este endpoint:
        # - Consulta todos los autores
        # - Convierte cada autor a diccionario usando to_dict()
        # - Devuelve la lista en formato JSON
        autores = Author.query.order_by(Author.id).all()
        return jsonify([a.to_dict() for a in autores]), 200

    @app.route('/authors', methods=['POST'])
    def add_author():
        """
        Agrega un nuevo autor
        El cuerpo de la solicitud debe incluir un JSON con el campo "name"
        """
        # Implementa este endpoint:
        # - Obtiene los datos JSON de la solicitud
        # - Crea un nuevo autor con el nombre proporcionado
        # - Lo guarda en la base de datos
        # - Devuelve el autor creado con código 201
        data = request.get_json(silent=True) or {}
        name = data.get("name")

        if not name or not isinstance(name, str):
            return jsonify({"error": "Field 'name' is required"}), 400
        
        autor = Author(name=name)
        db.session.add(autor)
        db.session.commit()

        return jsonify(autor.to_dict()), 201

    @app.route('/authors/<int:author_id>', methods=['GET'])
    def get_author(author_id):
        """
        Obtiene los detalles de un autor específico y su lista de libros
        """
        # Implementa este endpoint:
        # - Busca el autor por ID (usa get_or_404 para gestionar el error 404)
        # - Devuelve los detalles del autor y su lista de libros
        autor = Author.query.get_or_404(author_id)
        payload = autor.to_dict()
        payload["books"] = [b.to_dict() for b in autor.books]
        return jsonify(payload), 200

    # Endpoints de Libros
    @app.route('/books', methods=['GET'])
    def get_books():
        """
        Devuelve la lista completa de libros
        """
        # Implementa este endpoint:
        # - Consulta todos los libros
        # - Convierte cada libro a diccionario
        # - Devuelve la lista en formato JSON
        libros = Book.query.order_by(Book.id).all()
        return jsonify([b.to_dict() for b in libros]), 200

    @app.route('/books', methods=['POST'])
    def add_book():
        """
        Agrega un nuevo libro
        El cuerpo de la solicitud debe incluir JSON con campos "title", "author_id", y "year" (opcional)
        """
        # Implementa este endpoint:
        # - Obtiene los datos JSON de la solicitud
        # - Crea un nuevo libro con título, autor_id y año (opcional)
        # - Lo guarda en la base de datos
        # - Devuelve el libro creado con código 201
        data = request.get_json(silent=True) or {}
        title = data.get("title")
        author_id = data.get("author_id")
        year = data.get("year", None)

        if not title or not isinstance(title, str):
            return jsonify({"error": "Field 'title' is required"}), 400
        if author_id is None or not isinstance(author_id, int):
            return jsonify({"error": "Field 'author_id' is required and must be int"}), 400

        # Verificar que el autor existe
        Author.query.get_or_404(author_id)

        if year is not None:
            try:
                year = int(year)
            except (TypeError, ValueError):
                return jsonify({"error": "Field 'year' must be an integer"}), 400

        libro = Book(title=title, author_id=author_id, year=year)
        db.session.add(libro)
        db.session.commit()

        return jsonify(libro.to_dict()), 201


    @app.route('/books/<int:book_id>', methods=['GET'])
    def get_book(book_id):
        """
        Obtiene un libro específico por su ID
        """
        # Implementa este endpoint:
        # - Busca el libro por ID (usa get_or_404 para gestionar el error 404)
        # - Devuelve los detalles del libro
        libro = Book.query.get_or_404(book_id)
        return jsonify(libro.to_dict()), 200

    @app.route('/books/<int:book_id>', methods=['DELETE'])
    def delete_book(book_id):
        """
        Elimina un libro específico por su ID
        """
        # Implementa este endpoint:
        # - Busca el libro por ID (usa get_or_404)
        # - Elimina el libro de la base de datos
        # - Devuelve respuesta vacía con código 204
        libro = Book.query.get_or_404(book_id)
        db.session.delete(libro)
        db.session.commit()
        return ("", 204)


    @app.route('/books/<int:book_id>', methods=['PUT'])
    def update_book(book_id):
        """
        Actualiza la información de un libro existente
        El cuerpo puede incluir "title" y/o "year"
        """
        # Implementa este endpoint:
        # - Obtiene los datos JSON de la solicitud
        # - Busca el libro por ID (usa get_or_404)
        # - Actualiza los campos proporcionados (título y/o año)
        # - Guarda los cambios en la base de datos
        # - Devuelve el libro actualizado
        data = request.get_json(silent=True) or {}
        libro = Book.query.get_or_404(book_id)

        if "title" in data:
            if data["title"] is None or not isinstance(data["title"], str) or data["title"] == "":
                return jsonify({"error": "Field 'title' must be a non-empty string"}), 400
            libro.title = data["title"]

        if "year" in data:
            if data["year"] is None:
                libro.year = None
            else:
                try:
                    libro.year = int(data["year"])
                except (TypeError, ValueError):
                    return jsonify({"error": "Field 'year' must be an integer"}), 400

        db.session.commit()
        return jsonify(libro.to_dict()), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
