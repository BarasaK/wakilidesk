from django import forms

from documents.models import Document, DocumentCategory
from matters.models import Matter


class DocumentUploadForm(forms.ModelForm):
    file = forms.FileField()

    class Meta:
        model = Document
        fields = (
            "matter",
            "title",
            "document_type",
            "document_date",
            "reference_number",
            "description",
            "source",
            "confidentiality_level",
        )

    def __init__(self, *args, firm, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["matter"].queryset = Matter.objects.filter(firm=firm).order_by("-opened_date", "matter_number")
        self.fields["document_type"].queryset = DocumentCategory.objects.filter(
            firm=firm, is_active=True
        ).order_by("name")


class DocumentMetadataForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = (
            "title",
            "document_type",
            "document_date",
            "reference_number",
            "description",
            "source",
            "confidentiality_level",
        )

    def __init__(self, *args, firm, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document_type"].queryset = DocumentCategory.objects.filter(
            firm=firm, is_active=True
        ).order_by("name")


class DocumentVersionUploadForm(forms.Form):
    file = forms.FileField()


class DocumentCategoryForm(forms.ModelForm):
    class Meta:
        model = DocumentCategory
        fields = ("name", "is_active")
