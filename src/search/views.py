from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from search.services import global_search as run_global_search


@login_required
def global_search(request):
    firm = request.current_firm
    if firm is None:
        return redirect("firm_onboarding")
    query = request.GET.get("q", "")
    results = run_global_search(firm=firm, user=request.user, query=query)
    return render(request, "search/global.html", {"firm": firm, "query": query, "results": results})
