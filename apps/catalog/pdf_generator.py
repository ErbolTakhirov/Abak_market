# ==============================================
# PDF CATALOG GENERATOR
# ==============================================
"""
Generate PDF catalogs for WhatsApp bot distribution.
"""

import os
import io
from datetime import datetime
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import logging

logger = logging.getLogger(__name__)


class CatalogPDFGenerator:
    """
    Generate professional PDF catalogs from products.
    """
    
    def __init__(self):
        self.page_size = A4
        self.margin = 2 * cm
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Configure custom paragraph styles."""
        # Try to register a Cyrillic-supporting font
        try:
            # Use DejaVu fonts which support Cyrillic
            font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf')
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('DejaVu', font_path))
                base_font = 'DejaVu'
            else:
                base_font = 'Helvetica'
        except Exception:
            base_font = 'Helvetica'
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CatalogTitle',
            fontName=base_font,
            fontSize=24,
            leading=28,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=20
        ))
        
        # Category header style
        self.styles.add(ParagraphStyle(
            name='CategoryHeader',
            fontName=base_font,
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#27ae60'),
            spaceBefore=15,
            spaceAfter=10
        ))
        
        # Product name style
        self.styles.add(ParagraphStyle(
            name='ProductName',
            fontName=base_font,
            fontSize=12,
            leading=14,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        # Product description style
        self.styles.add(ParagraphStyle(
            name='ProductDesc',
            fontName=base_font,
            fontSize=9,
            leading=11,
            textColor=colors.HexColor('#7f8c8d')
        ))
        
        # Price style
        self.styles.add(ParagraphStyle(
            name='ProductPrice',
            fontName=base_font,
            fontSize=14,
            leading=16,
            textColor=colors.HexColor('#e74c3c')
        ))
    
    def generate(self, products, category=None):
        """
        Generate PDF catalog and return file path.
        
        Args:
            products: QuerySet of products
            category: Optional category to filter by
        
        Returns:
            str: Path to generated PDF file
        """
        # Create output directory
        output_dir = os.path.join(settings.MEDIA_ROOT, 'catalogs')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if category:
            filename = f"catalog_{category.slug}_{timestamp}.pdf"
        else:
            filename = f"catalog_full_{timestamp}.pdf"
        
        output_path = os.path.join(output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Build content
        story = self._build_story(products, category)
        
        # Generate PDF
        doc.build(story)
        
        logger.info(f"Generated PDF catalog: {output_path}")
        
        # Return relative path for Django FileField
        return os.path.join('catalogs', filename)
    
    def _build_story(self, products, category=None):
        """Build PDF story (content) from products."""
        story = []
        
        # Title
        title = category.name if category else settings.COMPANY_NAME
        story.append(Paragraph(title, self.styles['CatalogTitle']))
        
        # Subtitle with date
        subtitle = f"Каталог товаров • {datetime.now().strftime('%d.%m.%Y')}"
        story.append(Paragraph(subtitle, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Contact info
        contact_info = f"""
        📞 {settings.COMPANY_PHONE}<br/>
        📍 {settings.COMPANY_ADDRESS}<br/>
        💬 WhatsApp: {settings.COMPANY_WHATSAPP}
        """
        story.append(Paragraph(contact_info, self.styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Group products by category if showing all
        if category:
            story.extend(self._build_category_section(category, products))
        else:
            # Group by category
            from .models import Category
            categories = Category.objects.filter(
                is_active=True,
                products__in=products
            ).distinct().order_by('order', 'name')
            
            for cat in categories:
                cat_products = products.filter(category=cat)
                if cat_products.exists():
                    story.extend(self._build_category_section(cat, cat_products))
                    story.append(PageBreak())
        
        return story
    
    def _build_category_section(self, category, products):
        """Build section for a category."""
        elements = []
        
        # Category header
        header = f"{category.icon} {category.name}"
        elements.append(Paragraph(header, self.styles['CategoryHeader']))
        elements.append(Spacer(1, 10))
        
        # Products table
        table_data = []
        
        for product in products:
            # Product row
            name = Paragraph(product.name, self.styles['ProductName'])
            desc = Paragraph(
                product.short_description[:100] if product.short_description else '',
                self.styles['ProductDesc']
            )
            price = Paragraph(product.formatted_price, self.styles['ProductPrice'])
            
            # Try to add image
            try:
                if product.image and os.path.exists(product.image.path):
                    img = RLImage(product.image.path, width=2*cm, height=2*cm)
                else:
                    img = ''
            except Exception:
                img = ''
            
            table_data.append([img, [name, desc], price])
        
        if table_data:
            # Create table
            table = Table(
                table_data,
                colWidths=[2.5*cm, 10*cm, 3.5*cm],
                repeatRows=0
            )
            
            table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#ecf0f1')),
            ]))
            
            elements.append(table)
        
        return elements
