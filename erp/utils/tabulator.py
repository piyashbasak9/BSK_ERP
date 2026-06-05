from django.core.paginator import Paginator
from django.db.models import Q

class TabulatorGrid:
    def __init__(self, request_params, queryset, search_fields=None):
        self.params = request_params
        self.queryset = queryset
        self.page = int(self.params.get('page', 1))
        self.size = int(self.params.get('size', 20))
        self.search = self.params.get('search', '')
        self.sort_field = self.params.get('sort', 'id')
        self.sort_dir = self.params.get('order', 'asc')
        self.search_fields = search_fields or []

    def get_queryset(self):
        qs = self.queryset
        if self.search and self.search_fields:
            q_filter = Q()
            for field in self.search_fields:
                q_filter |= Q(**{f"{field}__icontains": self.search})
            qs = qs.filter(q_filter)
        if self.sort_field:
            order_by = self.sort_field if self.sort_dir == 'asc' else f'-{self.sort_field}'
            qs = qs.order_by(order_by)
        return qs

    def get_response(self):
        qs = self.get_queryset()
        paginator = Paginator(qs, self.size)
        page_obj = paginator.get_page(self.page)
        data = list(page_obj.object_list.values())
        return {
            'last_page': paginator.num_pages,
            'data': data,
            'current_page': self.page,
        }