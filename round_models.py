"""打球場次 · PostgreSQL / SQLite 持久化模型"""

from __future__ import annotations

from datetime import date, datetime

from models import db


class GolfRound(db.Model):
    """
    一場 18 洞記分（含進行中草稿）。
    external_id：對外 round id（URL、rounds.json 舊 id），唯一。
    """

    __tablename__ = "golf_rounds"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    creator_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="completed", index=True)

    course_id = db.Column(db.String(64), nullable=True)
    tee_id = db.Column(db.String(32), nullable=True)
    course_name = db.Column(db.String(200), nullable=True)
    tee_name = db.Column(db.String(80), nullable=True)
    par_total = db.Column(db.Integer, nullable=True)
    yardage_total = db.Column(db.Integer, nullable=True)
    pars_json = db.Column(db.JSON, nullable=True)

    note = db.Column(db.Text, nullable=True, default="")
    played_date = db.Column(db.String(10), nullable=True, index=True)
    played_time = db.Column(db.String(8), nullable=True)
    user_email = db.Column(db.String(255), nullable=True)

    draft_players_json = db.Column(db.JSON, nullable=True)
    draft_scores_json = db.Column(db.JSON, nullable=True)
    draft_hole_index = db.Column(db.Integer, nullable=True, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    creator = db.relationship("User", foreign_keys=[creator_user_id])
    participants = db.relationship(
        "RoundParticipant",
        back_populates="round",
        cascade="all, delete-orphan",
        order_by="RoundParticipant.sort_index",
    )

    def participant_user_ids(self) -> list[int]:
        ids: set[int] = set()
        if self.creator_user_id:
            ids.add(int(self.creator_user_id))
        for p in self.participants:
            if p.user_id:
                ids.add(int(p.user_id))
        return sorted(ids)


class RoundParticipant(db.Model):
    """一場中的單位球友成績（已完成場次）。"""

    __tablename__ = "round_participants"

    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(
        db.Integer,
        db.ForeignKey("golf_rounds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    player_name = db.Column(db.String(80), nullable=False)
    sort_index = db.Column(db.Integer, nullable=False, default=0)

    total_score = db.Column(db.Integer, nullable=True)
    to_par = db.Column(db.Integer, nullable=True)
    front9 = db.Column(db.Integer, nullable=True)
    back9 = db.Column(db.Integer, nullable=True)
    front_to_par = db.Column(db.Integer, nullable=True)
    back_to_par = db.Column(db.Integer, nullable=True)
    birdies = db.Column(db.Integer, nullable=True)
    pars_count = db.Column(db.Integer, nullable=True)
    bogeys = db.Column(db.Integer, nullable=True)
    double_plus = db.Column(db.Integer, nullable=True)

    round = db.relationship("GolfRound", back_populates="participants")
    user = db.relationship("User", foreign_keys=[user_id])
    hole_scores = db.relationship(
        "HoleScore",
        back_populates="participant",
        cascade="all, delete-orphan",
        order_by="HoleScore.hole_number",
    )


class HoleScore(db.Model):
    """單洞桿數。"""

    __tablename__ = "hole_scores"

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("round_participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hole_number = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    par = db.Column(db.Integer, nullable=False)
    diff = db.Column(db.Integer, nullable=False)
    label = db.Column(db.String(20), nullable=True)

    participant = db.relationship("RoundParticipant", back_populates="hole_scores")

    __table_args__ = (
        db.UniqueConstraint("participant_id", "hole_number", name="uq_hole_per_participant"),
    )
