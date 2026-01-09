from django import template

from cards.services import edits_remaining

register = template.Library()


@register.simple_tag
def edits_left(profile):
    remaining = edits_remaining(profile)
    if remaining is None:
        return "Unlimited"
    return str(remaining)
