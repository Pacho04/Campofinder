from flask_login import LoginManager
import pymysql
from flask import current_app, g


login_manager = LoginManager()
login_manager.login_view = "auth.login"


class MySQLWrapper:
	"""Light wrapper that provides `mysql.connection` similar to flask_mysqldb.

	It uses PyMySQL and stores the connection in `flask.g` so it's reused
	during the request and closed on teardown.
	"""

	def init_app(self, app):
		self.app = app

		@app.teardown_appcontext
		def _close_connection(exc=None):
			conn = g.pop('_mysql_conn', None)
			if conn is not None:
				try:
					conn.close()
				except Exception:
					pass

	@property
	def connection(self):
		# lazy create connection and store in g
		if '_mysql_conn' not in g:
			cfg = current_app.config
			g._mysql_conn = pymysql.connect(
				host=cfg.get('MYSQL_HOST', 'localhost'),
				user=cfg.get('MYSQL_USER', 'root'),
				password=cfg.get('MYSQL_PASSWORD', ''),
				db=cfg.get('MYSQL_DB', ''),
				charset='utf8mb4',
				cursorclass=pymysql.cursors.Cursor,
			)
		return g._mysql_conn


mysql = MySQLWrapper()
