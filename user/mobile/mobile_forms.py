from django import forms
from user.models import ClientProfile, ConditionType, SupportType, CertificationType
from user.models import VolunteerProfile,TaskType,PVGLevelType
import json
import datetime

class MobileClientProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        exclude = ['user_profile', 'id']

    def __init__(self, *args, **kwargs):
        print("🔥🔥🔥 INIT 被调用了！！！")
        super().__init__(*args, **kwargs)

        # ✅ 删除自动推导的多选字段，防止覆盖 clean_*
        for field in ['conditions', 'support_areas', 'certifications']:
            self.fields.pop(field, None)
            # if field in self.fields:
            #     del self.fields[field]

    def save(self, commit=True):
        instance = super().save(commit=False)  # 先保存主字段
        if commit:
            instance.save()

            # 多对多字段需要手动 set
            if 'conditions' in self.cleaned_data:
                instance.conditions.set(self.cleaned_data['conditions'])
            if 'support_areas' in self.cleaned_data:
                instance.support_areas.set(self.cleaned_data['support_areas'])
            if 'certifications' in self.cleaned_data:
                instance.certifications.set(self.cleaned_data['certifications'])

        return instance

    def parse_list_field(self, field_name):
        raw = self.data.get(field_name)
        if not raw:
            return []
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raw = [raw]
        return raw if isinstance(raw, list) else [raw]

    def clean_conditions(self):
        print("✅ clean_conditions 被触发了")
        raw = self.parse_list_field('conditions')
        print('🧪 清洗后的 conditions:', raw)
        qs = ConditionType.objects.filter(name__in=raw)
        print('🧪 匹配 conditions:', list(qs.values_list('name', flat=True)))
        # if len(qs) != len(raw):
        #     raise forms.ValidationError('Some condition values are invalid.')
        matched_names = list(qs.values_list('name', flat=True))
        missing = set(raw) - set(matched_names)
        if missing:
            raise forms.ValidationError(f'Some condition values are invalid: {missing}')
        return qs

    def clean_support_areas(self):
        raw = self.parse_list_field('support_areas')
        print('🧪 清洗后的 support_areas:', raw)
        qs = SupportType.objects.filter(name__in=raw)
        print('🧪 匹配 support_areas:', list(qs.values_list('name', flat=True)))
        if len(qs) != len(raw):
            raise forms.ValidationError('Some support area values are invalid.')
        return qs

    def clean_certifications(self):
        raw = self.parse_list_field('certifications')
        print('🧪 清洗后的 certifications:', raw)
        qs = CertificationType.objects.filter(name__in=raw)
        print('🧪 匹配 certifications:', list(qs.values_list('name', flat=True)))
        if len(qs) != len(raw):
            raise forms.ValidationError('Some certification values are invalid.')
        return qs

class MobileVolunteerProfileForm(forms.ModelForm):
    class Meta:
        model = VolunteerProfile
        exclude = ['user_profile', 'id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 全部设为非必填，便于测试
        for field in self.fields.values():
            field.required = False

        # 移除自动推导的多选字段，防止类型不兼容（尤其是 JSON 字符串进来时）
        for field in ['preferred_tasks', 'pvg_level']:
            self.fields.pop(field, None)

    def save(self, commit=True):
        instance = super().save(commit=False)

        # ✅ 兜底处理，防止 NOT NULL 错误
        if instance.availability in [None, '']:
            instance.availability = {}
        if instance.available_days is None:
            instance.available_days = []
        if instance.available_start_time is None:
            instance.available_start_time = datetime.time(0, 0)
        if instance.available_end_time is None:
            instance.available_end_time = datetime.time(23, 59)

        if commit:
            instance.save()

            if 'preferred_tasks' in self.cleaned_data:
                print("📌 开始保存 preferred_tasks:", self.cleaned_data.get('preferred_tasks'))
                instance.preferred_tasks.set(self.cleaned_data['preferred_tasks'])

            if 'pvg_level' in self.cleaned_data:
                print("📌 开始保存 pvg_level:", self.cleaned_data.get('pvg_level'))
                instance.pvg_level = self.cleaned_data['pvg_level']
                instance.save()

        return instance

    def parse_list_field(self, field_name):
        if hasattr(self.data, 'getlist'):
            raw = self.data.getlist(field_name)
        else:
            raw = self.data.get(field_name)

        if not raw:
            return []

        if isinstance(raw, list):
            return raw

        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
                return raw if isinstance(raw, list) else [raw]
            except json.JSONDecodeError:
                return [raw]

        return [raw]

    def clean_preferred_tasks(self):
        print("🔥 clean_preferred_tasks() 被调用")
        raw = self.parse_list_field('preferred_tasks')
        print("📥 raw from parse_list_field:", raw)

        qs = TaskType.objects.filter(name__in=raw)
        matched_names = list(qs.values_list('name', flat=True))
        print("✅ matched:", matched_names)

        missing = set(raw) - set(matched_names)
        if missing:
            print("❌ missing:", missing)
            raise forms.ValidationError(f'Some preferred task values are invalid: {missing}')
        # return qs
        return list(qs.values_list('id', flat=True))

    def clean_pvg_level(self):
        code = self.data.get('pvg_level')
        print("📥 原始 pvg_level 值：", self.data.get('pvg_level'))
        print("📏 类型：", type(self.data.get('pvg_level')))
        valid_codes = list(PVGLevelType.objects.values_list('code', flat=True))
        if code not in valid_codes:
            raise forms.ValidationError(f'Invalid PVG level: {code}')
        return code