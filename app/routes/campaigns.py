"""
app/routes/campaigns.py — Campaign builder blueprint.
"""
from __future__ import annotations

from flask import (
    Blueprint, flash, jsonify, redirect, render_template,
    request, url_for
)
from flask_login import current_user, login_required

from app.extensions import db
from app.models.attachment import Attachment
from app.models.campaign import Campaign
from app.models.template import Template

campaigns_bp = Blueprint("campaigns", __name__, url_prefix="/campaigns")


@campaigns_bp.route("/")
@login_required
def index():
    """Campaign list page."""
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return render_template("campaigns/index.html", campaigns=campaigns)


@campaigns_bp.route("/builder")
@campaigns_bp.route("/builder/<int:campaign_id>")
@login_required
def builder(campaign_id: int = None):
    """Campaign builder page (create or edit)."""
    campaign = Campaign.query.get(campaign_id) if campaign_id else None
    templates = Template.query.filter_by(is_active=True).all()
    attachments = Attachment.query.filter_by(is_active=True).all()
    return render_template(
        "campaigns/builder.html",
        campaign=campaign,
        templates=templates,
        attachments=attachments,
    )


@campaigns_bp.route("/save", methods=["POST"])
@login_required
def save():
    """Save a new or updated campaign."""
    data = request.get_json() or request.form
    campaign_id = data.get("campaign_id")

    if campaign_id:
        campaign = Campaign.query.get_or_404(int(campaign_id))
    else:
        campaign = Campaign(created_by=current_user.id)
        db.session.add(campaign)

    campaign.name = data.get("name", "Unnamed Campaign")
    campaign.subject = data.get("subject", "")
    campaign.body_html = data.get("body_html", "")
    campaign.body_text = data.get("body_text", "")
    campaign.audience = data.get("audience", "all")
    campaign.cc = data.get("cc", "")
    campaign.bcc = data.get("bcc", "")
    campaign.daily_limit = int(data.get("daily_limit", 200))
    campaign.delay_seconds = int(data.get("delay_seconds", 3))

    att_id = data.get("attachment_id")
    campaign.attachment_id = int(att_id) if att_id else None

    tpl_id = data.get("template_id")
    campaign.template_id = int(tpl_id) if tpl_id else None

    db.session.commit()
    return jsonify({"status": "saved", "campaign_id": campaign.id})


@campaigns_bp.route("/<int:campaign_id>/delete", methods=["POST"])
@login_required
def delete(campaign_id: int):
    """Delete a campaign."""
    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    return jsonify({"status": "deleted"})


@campaigns_bp.route("/api")
@login_required
def api_list():
    """JSON list of all campaigns."""
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return jsonify({"campaigns": [c.to_dict() for c in campaigns]})
