import os
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import db, setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def randint_except(ids, exclude=[]):
    pool = [id for id in ids if id not in exclude]
    # pool = list(set(range(start, stop+1))
    #                 -set([exclude] if isinstance(exclude, int)
    #                     else exclude)
    #             )
    return random.choice(pool)

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"*": {"origins": "*"}})    

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route("/categories")
    def retrieve_categories():
        error = False
        try:
            categories = Category.query.order_by(Category.id).all()
        except Exception as e:
            error = True

        if len(categories) == 0:
            abort(404)
        elif error:
            abort(422)

        return jsonify(
            {
                "success": True,
                "categories": [categorie.type for categorie in categories],
                "total_categories": len(Category.query.all()),
            }
        )    


    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route("/questions", methods=['GET'])
    def retrieve_questions():
        error = False

        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        categories = [category.type for category in Category.query.order_by(Category.id).all()]
        if 0 in (len(current_questions), len(current_questions), len(categories)):
            abort(404)
        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len([question for question in selection]),
                "current_category": None,
                "categories": categories,
            }
        )

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route("/questions/<int:question_id>", methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question == None:
                abort(404)

            question.delete()           
            
            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "total_questions": len(Question.query.all()),
                }
            ) 
        except Exception as e :
            print(e)
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()
        search = body.get("searchTerm", None)

        try:
            if search:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike("%{}%".format(search))
                )
                questions = paginate_questions(request, selection)
                current_category = Category.query.get(1)

                return jsonify(
                    {
                        "success": True,
                        "questions": questions,
                        "total_questions": len([question for question in selection]),
                        "current_category": current_category.type,
                    }
                )
            else:
                Question(
                    question = body.get('question', None),
                    answer = body.get('answer', None),
                    difficulty = body.get('difficulty', None),
                    category = body.get('category', None),
                ).insert()
                
                return jsonify(
                    {
                        "success": True,
                    }
                )                
        except:
            abort(422)    

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route("/categories/<int:category_id>/questions", methods=['GET'])
    def questions_by_cat(category_id):

        selection = Question.query.filter(Question.category==category_id).order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        current_category = Category.query.get(category_id)

        if len(current_questions) == 0 or current_category == None:
            abort(404)
        
        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len([question for question in selection]),
                "current_category": current_category.type,
            }
        )

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route("/quizzes", methods=['POST'])
    def quizzes():
        body = request.get_json()
        previous_questions = body.get("previous_questions", None)
        quiz_category = body.get("quiz_category", None)

        try:
            if quiz_category['type'] == 'click':
                questions = Question.query.order_by(Question.id).all()
            else:
                questions = Question.query.filter(Question.category==int(quiz_category['id'])+1).order_by(Question.id)

            if len([question for question in questions]) == 0:
                abort(404)

            questions_id = [question.id for question in questions]
            if questions_id != sorted(previous_questions):
                next_question_id = randint_except(questions_id, previous_questions)
                selection = Question.query.filter(Question.id == next_question_id)
                next_question = paginate_questions(request, selection)
            else:
                next_question = ''

            return jsonify(
                {
                    "success": True,
                    "question": next_question,
                }
            )
        except Exception as e:
            print(e)
            abort(422)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(400)
    def bad_request(error):
        return (
            jsonify({"success": False, "error": 400, "message": "bad request"}),
            400,
        )
    
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    return app

