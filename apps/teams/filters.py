from django.db.models import Q


def build_team_q(request):
    q_name = request.query_params.get('name')
    q_owner = request.query_params.get('owner')
    q_member = request.query_params.get('members')
    q_search = request.query_params.get('q')

    conds = Q()
    if q_name:
        conds &= Q(name__icontains = q_name)
    if q_owner:
        conds &= Q(owner_id = q_owner)
    if q_member:
        conds &= (Q(members__id = q_member) | Q(owner_id = q_member))
    if q_search:
        conds &= (
            Q(name__icontains = q_name) |
            Q(description__icontains = q_search) |
            Q(owner__first_name__icontains = q_search) |
            Q(owner__last_name__icontains = q_search)
        )
    return conds

def build_membership_q(request,team):
    role = request.query_params.get('role')
    user_q = request.query_params.get('user')

    conds = Q(team=team)
    if role:
        conds &= Q(role = role)
    if user_q:
        conds &= Q(user_first_name = user_q)
    return conds