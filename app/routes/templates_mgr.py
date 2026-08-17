"""
app/routes/templates_mgr.py — Email templates management blueprint.
"""
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models.template import Template

templates_bp = Blueprint("templates", __name__, url_prefix="/templates")


@templates_bp.route("/")
@login_required
def index():
    """Template manager page."""
    templates = Template.query.order_by(Template.created_at.desc()).all()
    return render_template("templates_mgr/index.html", templates=templates)


@templates_bp.route("/save", methods=["POST"])
@login_required
def save():
    """Create or update a template."""
    data = request.get_json() or request.form.to_dict()
    tid = data.get("template_id")

    if tid:
        tpl = Template.query.get_or_404(int(tid))
    else:
        tpl = Template(created_by=current_user.id)
        db.session.add(tpl)

    tpl.name = data.get("name", "Unnamed Template")
    tpl.subject = data.get("subject", "")
    tpl.body_html = data.get("body_html", "")
    tpl.body_text = data.get("body_text", "")
    tpl.category = data.get("category", "general")
    tpl.description = data.get("description", "")
    tpl.is_active = True

    db.session.commit()
    return jsonify({"status": "saved", "template_id": tpl.id})


@templates_bp.route("/<int:template_id>")
@login_required
def get_template(template_id: int):
    """Return template data as JSON."""
    tpl = Template.query.get_or_404(template_id)
    return jsonify(tpl.to_dict())


@templates_bp.route("/<int:template_id>/delete", methods=["POST"])
@login_required
def delete(template_id: int):
    """Delete a template."""
    tpl = Template.query.get_or_404(template_id)
    tpl.is_active = False
    db.session.commit()
    return jsonify({"status": "deleted"})


@templates_bp.route("/default-templates")
@login_required
def default_templates():
    """Seed and return the default email templates."""
    _seed_default_templates()
    templates = Template.query.filter_by(is_active=True).all()
    return jsonify({"templates": [t.to_dict() for t in templates]})


def _seed_default_templates() -> None:
    """Create built-in templates if none exist."""
    if Template.query.count() > 0:
        return

    templates = [
        {
            "name": "Business Introduction",
            "subject": "Partnership Opportunity — {{company}}",
            "body_html": """
<p>Dear {{name}},</p>
<p>I hope this email finds you well. We are writing to introduce ourselves as a leading exporter of premium <strong>Singing Bowls</strong> from Nepal.</p>
<p>Our products are handcrafted by skilled artisans and are in high demand across {{country}} and globally. We would love to explore a business partnership with <strong>{{company}}</strong>.</p>
<p>Please find our product catalog attached. We look forward to hearing from you.</p>
<p>Warm regards,<br>Export Team</p>
""",
            "category": "business",
        },
        {
            "name": "Individual Buyer Outreach",
            "subject": "Exclusive Singing Bowls — Special Offer for You",
            "body_html": """
<p>Dear {{name}},</p>
<p>We came across your profile and believe our handcrafted Singing Bowls would be a perfect fit for you.</p>
<p>As a special introductory offer, we are offering a <strong>15% discount</strong> on your first order.</p>
<p>Visit our catalog or reply to this email to know more.</p>
<p>Best wishes,<br>Export Team</p>
""",
            "category": "individual",
        },
        {
            "name": "Follow-Up Email",
            "subject": "Following Up — Singing Bowls Inquiry",
            "body_html": """
<p>Dear {{name}},</p>
<p>This is a gentle follow-up to our previous email regarding our Singing Bowls.</p>
<p>We would love to discuss how we can serve <strong>{{company}}</strong> with our premium products. Please let us know a convenient time to connect.</p>
<p>Thank you,<br>Export Team</p>
""",
            "category": "general",
        },
    ]

    for t in templates:
        tpl = Template(**t, is_active=True, is_default=True)
        db.session.add(tpl)
    db.session.commit()
