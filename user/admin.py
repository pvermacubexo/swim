from django.contrib import admin
from .models import User, ReviewRate, Profile, StudentProfile, WeekTimeSlots, BreakTime
from django.contrib.auth.models import Group


class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'mobile_no', 'user_type', 'verified', 'pk')
    search_fields = ['email', 'mobile_no']
    exclude = ('deactivate', 'groups', 'user_permissions', 'last_login')

    def get_queryset(self, request):
        if request.user.is_instructor:
            return self.model.objects.filter(id=request.user.id)
        else:
            return self.model.objects.all()

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['user_type', 'password']
        else:
            return []


class ReviewRateAdmin(admin.ModelAdmin):
    list_display = ('rated_by', 'rating', 'review')
    search_fields = ['rated_by', 'rating']

    def get_queryset(self, request):
        if request.user.is_instructor:
            return self.model.objects.filter(rated_to__id=request.user.id)
        else:
            return self.model.objects.all()

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['rated_by', 'rated_to']
        else:
            return []


class BreakTimeInline(admin.TabularInline):
    model = BreakTime
    extra = 1


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'language',)
    inlines = [BreakTimeInline]

    # list_filter = ['user__date_joined']

    def get_queryset(self, request):
        if request.user.is_instructor:
            return self.model.objects.filter(user__id=request.user.id)
        else:
            return self.model.objects.all()

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['user', 'slug', 'url']
        else:
            return []


class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'father_name', 'mother_name', 'DateOfBirth')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['user', 'instructor']
        else:
            return []


class WeekTimeSlotsAdmin(admin.ModelAdmin):
    list_display = (
        'instructor',
        'monday_startTime_slot',
        'monday_endTime_slot',
        'tuesday_startTime_slot',
        'tuesday_endTime_slot',
        'wednesday_startTime_slot',
        'wednesday_endTime_slot',
        'thursday_startTime_slot',
        'thursday_endTime_slot',
        'friday_startTime_slot',
        'friday_endTime_slot',
        'saturday_startTime_slot',
        'saturday_endTime_slot',
        'sunday_startTime_slot',
        'sunday_endTime_slot',
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['instructor']
        else:
            return []


admin.site.register(User, UserAdmin)
admin.site.register(ReviewRate, ReviewRateAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.unregister(Group)
admin.site.register(StudentProfile, StudentProfileAdmin)
# admin.site.register(WeekTimeSlots, WeekTimeSlotsAdmin)
# admin.site.register(BreakTime)
