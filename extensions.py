"""Flask extensions（Blueprint 共用，避免循環引用）"""

from flask_mail import Mail

mail = Mail()
