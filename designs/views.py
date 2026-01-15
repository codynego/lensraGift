from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Design
from .serializers import DesignSerializer, DesignCreateSerializer
from rest_framework.permissions import AllowAny


class DesignListCreateView(APIView):
    # Change this to AllowAny so guests can POST
    permission_classes = [AllowAny]

    def get(self, request):
        # Keep your existing check for the GET list
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required to view designs."}, status=401)
        
        designs = Design.objects.filter(user=request.user)
        serializer = DesignSerializer(designs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DesignCreateSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user if request.user.is_authenticated else None
            # Also capture session_id if you added it to your model
            session_id = request.data.get('session_id')
            
            design = serializer.save(user=user, session_id=session_id)
            
            return Response(
                DesignSerializer(design).data, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DesignDetailView(APIView):
    """Retrieve, update, or delete a specific design."""
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return Design.objects.get(pk=pk)
        except Design.DoesNotExist:
            return None

    def get(self, request, pk):
        design = self.get_object(pk)
        if not design:
            return Response({"error": "Template not found"}, status=404)
        serializer = DesignSerializer(design)
        return Response(serializer.data)

    def patch(self, request, pk):
        """Update specific fields like is_featured or name."""
        design = self.get_object(pk)
        
        if not design:
            return Response({"error": "Template not found"}, status=404)
            
        # Security: Only the owner can edit
        if design.user != request.user:
            return Response({"error": "You do not have permission to edit this template"}, status=403)

        # partial=True allows us to update just one field (like is_featured)
        serializer = DesignSerializer(design, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        design = self.get_object(pk)
        
        if not design:
            return Response({"error": "Template not found"}, status=404)
            
        if design.user == request.user:
            design.delete()
            return Response({"message": "Template deleted successfully"}, status=204)
            
        return Response({"error": "Unauthorized"}, status=403)


class PublicDesignsView(APIView):
    """Returns a list of public designs."""
    permission_classes = [AllowAny]

    def get(self, request):
        public_designs = Design.objects.filter(is_featured=True)
        serializer = DesignSerializer(public_designs, many=True)
        return Response(serializer.data)