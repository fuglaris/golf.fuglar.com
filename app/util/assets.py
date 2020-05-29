from flask_assets import Bundle

bundles = {

	'golfcourse_js': Bundle(
		'js/golfcourse.js',
		output='gen/golfcourse_js.js',
        filters='jsmin'),

	'calendar_js': Bundle(
		'js/base.js',
		output='gen/calendar_js.js',
        filters='jsmin'),

	'stat_js': Bundle(
		'js/stat.js',
		output='gen/stat_js.js',
        filters='jsmin'),

	'main_js': Bundle(
        'vendor/js/jquery.js',
		'vendor/js/jquery-ui.min.js',
        'vendor/js/bootstrap.js',
        'vendor/js/bootstrap-notify.min.js',
        'vendor/js/paper-dashboard.js',
		'vendor/js/moment.min.js',
		'vendor/js/fullcalendar.js',
		'vendor/js/locale-all.js',
		'vendor/js/chartjs.js',
		output='gen/main_js.js',
        filters='jsmin'),

	'main_css': Bundle(
        'vendor/css/bootstrap.css',
        'vendor/css/bootstrap-theme.css',
		'vendor/css/bootstrap-social.css',
		'vendor/css/paper-dashboard.css',
		'vendor/css/font-awesome.min.css',
		'vendor/css/fullcalendar.css',
		'css/main.css',
		'vendor/css/flag-icon.css',
		output='gen/main_css.css',
        filters='cssmin'),

	'login_js': Bundle(
        'vendor/js/jquery.js',
        'vendor/js/bootstrap.js',
		output='gen/login.js',
        filters='jsmin'),

	'login_css': Bundle(
        'vendor/css/bootstrap.css',
        'vendor/css/bootstrap-theme.css',
		'vendor/css/font-awesome.css',
		'vendor/css/bootstrap-social.css',
        'css/login.css',
		output='gen/login.css',
        filters='cssmin')
}
