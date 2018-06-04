from app import app

if __name__ == '__main__':
    #app.config.from_object('config.DevelopmentConfig')
    app.config.from_object('config.ProductionConfig')
    app.run(debug=True)
