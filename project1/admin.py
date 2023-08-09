from datetime import date
from django.shortcuts import render
from django.urls import path
from django.contrib import admin
from pitch.custom_fnc import (
    create_day_of_month,
    create_empty_day_of_month,
    query_statistic,
)
from django.core.paginator import Paginator
from pitch.models import Order, Pitch
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

    def statistics_pitch(self, request, pk):
        pitch = Pitch.objects.get(pk=pk)
        last_month = date.today().month - 1
        year = date.today().year
        orders = Order.objects.raw(
            """SELECT 1 as id, day(time_start) as date, sum(cost) as revenue from orders 
                where pitch_id = %d and 
                      month(time_start) = %d and 
                      year(time_start) = %d 
                group by date"""
            % (pk, last_month, year)
        )
        data = create_empty_day_of_month()
        for order in orders:
            data[order.date - 1] = int(order.revenue)

        context = dict(
            **self.each_context(request),
            title="Statistics of pitch",
            pk=pk,
            labels=create_day_of_month(),
            data=data,
            pitch=pitch,
            last_month=last_month,
        )

        return render(request, "admin/statistic_pitch.html", context=context)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("statistic/", self.admin_view(self.statistic), name="statistics"),
            path(
                "statistic/<int:pk>/",
                self.admin_view(self.statistics_pitch),
                name="statistic-pitch",
            ),
        ]
        return my_urls + urls

    def get_app_list(self, request, _=None):
        app_list = super().get_app_list(request)
        app_list += [
            {
                "name": "statistics",
                "app_label": "statistics",
                "models": [
                    {
                        "name": "statistics",
                        "object_name": "statistics",
                        "admin_url": "/admin/statistic",
                        "view_only": True,
                    }
                ],
            }
        ]
        return app_list


my_admin_site = MyAdminSite()
