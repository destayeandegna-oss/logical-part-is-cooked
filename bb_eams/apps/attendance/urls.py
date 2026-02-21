from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CheckInView, CheckOutView, AttendanceHistoryView,
    DailyAttendanceView, AttendanceSummaryView, ShiftViewSet
)

router = DefaultRouter()
router.register(r'shifts', ShiftViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('check-in/', CheckInView.as_view(), name='check-in'),
    path('check-out/', CheckOutView.as_view(), name='check-out'),
    path('history/', AttendanceHistoryView.as_view(), name='attendance-history'),
    path('daily/', DailyAttendanceView.as_view(), name='daily-attendance'),
    path('summary/', AttendanceSummaryView.as_view(), name='attendance-summary'),
]