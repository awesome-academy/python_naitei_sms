from datetime import date
from django.shortcuts import render
from django.urls import path
from django.contrib import admin
from pitch.custom_fnc import query_statistic
from django.core.paginator import Paginator

from project1.settings import HOST


class MyAdminSite(admin.AdminSite):
    def statistic(self, request):
        "Monthly revenue including Course information, Total amount, Number of pitch bookings"

        last_month = date.today().month - 1
        pitches = query_statistic()
        paginator = Paginator(pitches, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = dict(
            **self.each_context(request),
            title="Statistics",
            page_obj=page_obj,
            month=last_month,
            host=HOST,
            is_paginated=True,
        )

        return render(request, "admin/revenue_statistic.html", context=context)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("statistic/", self.admin_view(self.statistic), name="statistic")
        ]
        return my_urls + urls

    def get_app_list(self, request, _=None):
        app_list = super().get_app_list(request)
        app_list += [
            {
                "name": "Statistics",
                "app_label": "statistics",
                "models": [
                    {
                        "name": "Sales statistics",
                        "object_name": "sales_statistics",
                        "admin_url": "/admin/statistic",
                        "view_only": True,
                    }
                ],
            }
        ]
        return app_list


my_admin_site = MyAdminSite()
