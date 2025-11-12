from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import SoftDeleteManager, TenantManager


class BaseViewSetMixin:
    """
    Mixin com funcionalidades comuns para viewsets
    """
    def get_queryset(self):
        """Retorna queryset filtrado por soft delete"""
        if hasattr(self, 'queryset') and self.queryset is not None:
            return self.queryset
        return self.get_serializer_class().Meta.model.objects.all()

    def perform_destroy(self, instance):
        """Implementa soft delete ao invés de delete físico"""
        if hasattr(instance, 'soft_delete'):
            instance.soft_delete()
        else:
            instance.delete()


class TenantViewSetMixin(BaseViewSetMixin):
    """
    Mixin para viewsets que lidam com tenants
    """
    def get_queryset(self):
        """Filtra queryset pelos clientes do usuário"""
        queryset = super().get_queryset()
        if hasattr(queryset, 'for_user'):
            return queryset.for_user(self.request.user)
        return queryset

    def perform_create(self, serializer):
        """Define o client baseado no usuário logado"""
        if hasattr(serializer.Meta.model, 'client'):
            user_client = self.request.user.client_members.first()
            if user_client:
                serializer.save(client=user_client.client)
            else:
                serializer.save()
        else:
            serializer.save()


class SoftDeleteViewSetMixin(BaseViewSetMixin):
    """
    Mixin para viewsets que lidam com soft delete
    """
    def get_queryset(self):
        """Retorna queryset sem objetos soft deleted"""
        queryset = super().get_queryset()
        if hasattr(queryset, 'with_deleted'):
            return queryset  # Já filtra automaticamente
        return queryset.filter(deleted_at__isnull=True)

    @api_view(['POST'])
    @permission_classes([permissions.IsAuthenticated])
    def restore_view(self, request, pk=None):
        """Endpoint para restaurar objeto soft deleted"""
        instance = get_object_or_404(self.get_queryset().with_deleted(), pk=pk)
        if hasattr(instance, 'restore'):
            instance.restore()
            return Response({'message': 'Objeto restaurado com sucesso'})
        return Response(
            {'error': 'Objeto não suporta restauração'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class FilterByClientMixin:
    """
    Mixin para filtrar por cliente do usuário
    """
    def get_queryset(self):
        """Filtra queryset pelos clientes do usuário"""
        queryset = super().get_queryset()
        user_clients = self.request.user.client_members.values_list('client_id', flat=True)
        return queryset.filter(client_id__in=user_clients)


class SearchMixin:
    """
    Mixin para funcionalidade de busca
    """
    search_fields = []
    search_param = 'search'

    def get_queryset(self):
        """Adiciona funcionalidade de busca ao queryset"""
        # Get base queryset from view's queryset attribute first
        if hasattr(self, 'queryset') and self.queryset is not None:
            queryset = self.queryset._clone()
        else:
            # Try to get from super() or model
            try:
                queryset = super().get_queryset()
            except AttributeError:
                queryset = self.get_serializer_class().Meta.model.objects.all()
        
        search_term = self.request.query_params.get(self.search_param)
        
        if search_term and self.search_fields:
            search_filters = None
            for field in self.search_fields:
                field_filter = Q(**{f"{field}__icontains": search_term})
                if search_filters is None:
                    search_filters = field_filter
                else:
                    search_filters |= field_filter
            
            if search_filters:
                queryset = queryset.filter(search_filters)
        
        return queryset


class PaginationMixin:
    """
    Mixin para paginação customizada
    """
    page_size = 20
    page_size_param = 'page_size'
    max_page_size = 100

    def get_queryset(self):
        """Aplica paginação ao queryset"""
        queryset = super().get_queryset()
        page_size = self.request.query_params.get(self.page_size_param, self.page_size)
        
        try:
            page_size = int(page_size)
            if page_size > self.max_page_size:
                page_size = self.max_page_size
        except (ValueError, TypeError):
            page_size = self.page_size
        
        return queryset


class AuditMixin:
    """
    Mixin para auditoria de mudanças
    """
    def perform_create(self, serializer):
        """Registra quem criou o objeto"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Registra quem atualizou o objeto"""
        serializer.save(updated_by=self.request.user)