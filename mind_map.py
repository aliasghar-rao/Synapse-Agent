"""
Mind map module for Drive-Manager Pro.
Implements a neural link-based mind map for file relationships.
"""

import math
import random
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPointF
from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath

import config


class MindMapCanvas(FigureCanvas):
    """Canvas widget to display the mind map using matplotlib"""
    
    node_clicked = pyqtSignal(str, str)  # node_id, node_type
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Set up figure appearance
        self.fig.patch.set_facecolor(config.COLORS['mind_map_bg'])
        self.ax.set_facecolor(config.COLORS['mind_map_bg'])
        self.ax.axis('off')
        
        # Initialize the graph
        self.graph = nx.Graph()
        self.pos = {}  # Node positions
        self.node_colors = {}
        self.node_sizes = {}
        self.node_types = {}
        self.edge_colors = {}
        self.labels = {}
        
        # For animations and interactions
        self.highlighted_node = None
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_step = 0
        
        # Enable interactions
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)
        
        # Set up the layout
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()
    
    def build_sample_graph(self):
        """Create a sample graph structure for demonstration"""
        self.graph.clear()
        
        # File nodes
        files = [
            ('script.py', 'file'),
            ('document.docx', 'file'),
            ('image.jpg', 'file'),
            ('presentation.pptx', 'file'),
            ('data.csv', 'file')
        ]
        
        # App nodes
        apps = [
            ('VSCode', 'app'),
            ('Word', 'app'),
            ('Photoshop', 'app'),
            ('PowerPoint', 'app'),
            ('Excel', 'app')
        ]
        
        # Tag nodes
        tags = [
            ('Python', 'tag'),
            ('Document', 'tag'),
            ('Image', 'tag'),
            ('Presentation', 'tag'),
            ('Data', 'tag'),
            ('ProjectX', 'tag')
        ]
        
        # Add nodes
        for name, node_type in files + apps + tags:
            self.graph.add_node(name)
            self.node_types[name] = node_type
        
        # Set node colors based on type
        for name, node_type in self.node_types.items():
            if node_type == 'file':
                self.node_colors[name] = config.COLORS['files']
                self.node_sizes[name] = config.MIND_MAP['node_size']['file']
            elif node_type == 'app':
                self.node_colors[name] = config.COLORS['primary']
                self.node_sizes[name] = config.MIND_MAP['node_size']['app']
            elif node_type == 'tag':
                self.node_colors[name] = config.COLORS['tools']
                self.node_sizes[name] = config.MIND_MAP['node_size']['tag']
        
        # Add edges (relationships)
        edges = [
            ('script.py', 'VSCode', 'dependency'),
            ('document.docx', 'Word', 'dependency'),
            ('image.jpg', 'Photoshop', 'dependency'),
            ('presentation.pptx', 'PowerPoint', 'dependency'),
            ('data.csv', 'Excel', 'dependency'),
            ('script.py', 'Python', 'tag'),
            ('document.docx', 'Document', 'tag'),
            ('image.jpg', 'Image', 'tag'),
            ('presentation.pptx', 'Presentation', 'tag'),
            ('data.csv', 'Data', 'tag'),
            ('script.py', 'ProjectX', 'project'),
            ('document.docx', 'ProjectX', 'project'),
            ('image.jpg', 'ProjectX', 'project')
        ]
        
        for source, target, edge_type in edges:
            self.graph.add_edge(source, target)
            if edge_type == 'dependency':
                self.edge_colors[(source, target)] = config.COLORS['primary']
            elif edge_type == 'tag':
                self.edge_colors[(source, target)] = config.COLORS['tools']
            elif edge_type == 'project':
                self.edge_colors[(source, target)] = config.COLORS['cloud']
        
        # Calculate layout
        self.pos = nx.spring_layout(self.graph, k=0.3, iterations=50)
        
        # Draw the graph
        self.draw_graph()
    
    def build_graph_from_files(self, files, tags, apps):
        """Build a graph based on actual file metadata"""
        self.graph.clear()
        self.node_colors = {}
        self.node_sizes = {}
        self.node_types = {}
        self.edge_colors = {}
        
        # Add file nodes
        for file in files:
            self.graph.add_node(file.name)
            self.node_types[file.name] = 'file'
            self.node_colors[file.name] = config.COLORS['files']
            self.node_sizes[file.name] = config.MIND_MAP['node_size']['file']
            
            # Connect to tags
            for tag in file.tags:
                if tag not in self.graph:
                    self.graph.add_node(tag)
                    self.node_types[tag] = 'tag'
                    self.node_colors[tag] = config.COLORS['tools']
                    self.node_sizes[tag] = config.MIND_MAP['node_size']['tag']
                
                self.graph.add_edge(file.name, tag)
                self.edge_colors[(file.name, tag)] = config.COLORS['tools']
                
            # Connect to apps
            for app in file.linked_apps:
                if app not in self.graph:
                    self.graph.add_node(app)
                    self.node_types[app] = 'app'
                    self.node_colors[app] = config.COLORS['primary']
                    self.node_sizes[app] = config.MIND_MAP['node_size']['app']
                
                self.graph.add_edge(file.name, app)
                self.edge_colors[(file.name, app)] = config.COLORS['primary']
        
        # Calculate layout
        self.pos = nx.spring_layout(self.graph, k=0.3, iterations=50)
        
        # Draw the graph
        self.draw_graph()
    
    def draw_graph(self):
        """Draw the network graph"""
        self.ax.clear()
        
        # Draw edges
        for edge in self.graph.edges():
            x1, y1 = self.pos[edge[0]]
            x2, y2 = self.pos[edge[1]]
            color = self.edge_colors.get(edge, self.edge_colors.get((edge[1], edge[0]), config.COLORS['border']))
            
            # Check if this edge connects to the highlighted node
            if self.highlighted_node and (edge[0] == self.highlighted_node or edge[1] == self.highlighted_node):
                alpha = 1.0
                width = config.MIND_MAP['edge_width'] + 0.5
            else:
                alpha = 0.7
                width = config.MIND_MAP['edge_width']
            
            self.ax.plot([x1, x2], [y1, y2], color=color, alpha=alpha, linewidth=width)
        
        # Draw nodes
        for node in self.graph.nodes():
            x, y = self.pos[node]
            size = self.node_sizes.get(node, 10)
            color = self.node_colors.get(node, config.COLORS['primary'])
            
            # Make highlighted node larger with animation
            if node == self.highlighted_node:
                size *= 1.2 + 0.2 * math.sin(self.animation_step * 0.2)
                alpha = 1.0
                edgecolor = 'white'
                linewidth = 2
            else:
                alpha = 0.9
                edgecolor = color
                linewidth = 1.5
            
            self.ax.scatter(x, y, s=size*100, color=color, alpha=alpha, 
                       edgecolor=edgecolor, linewidth=linewidth, zorder=3)
            
            # Draw labels with small offset for better readability
            label_offset = 0.01
            self.ax.text(x + label_offset, y + label_offset, node, 
                    fontsize=8, color='white', ha='center', va='center', zorder=4)
        
        # Set plot limits
        self.ax.set_xlim(-1.1, 1.1)
        self.ax.set_ylim(-1.1, 1.1)
        
        # Refresh canvas
        self.fig.tight_layout()
        self.draw()
    
    def highlight_node(self, node_id):
        """Highlight a node and start animation"""
        self.highlighted_node = node_id
        self.animation_step = 0
        if not self.animation_timer.isActive():
            self.animation_timer.start(50)  # 50 ms interval
        self.draw_graph()
    
    def update_animation(self):
        """Update animation state for highlighted node"""
        self.animation_step += 1
        if self.animation_step > 100:  # Reset after 100 steps
            self.animation_step = 0
        
        if self.highlighted_node:
            self.draw_graph()
    
    def on_click(self, event):
        """Handle mouse click events"""
        if event.inaxes != self.ax:
            return
        
        # Find the closest node to the click
        min_dist = float('inf')
        closest_node = None
        
        for node in self.graph.nodes():
            x, y = self.pos[node]
            dist = math.sqrt((event.xdata - x)**2 + (event.ydata - y)**2)
            
            # Scale the "clickable area" based on node size
            size_factor = self.node_sizes.get(node, 10) / 10
            threshold = 0.05 * size_factor
            
            if dist < threshold and dist < min_dist:
                min_dist = dist
                closest_node = node
        
        if closest_node:
            self.highlight_node(closest_node)
            node_type = self.node_types.get(closest_node, 'unknown')
            self.node_clicked.emit(closest_node, node_type)
    
    def on_hover(self, event):
        """Handle mouse hover events"""
        # Similar to on_click, but just for hover effects
        if event.inaxes != self.ax:
            return
            
        # Find the closest node to hover
        min_dist = float('inf')
        closest_node = None
        
        for node in self.graph.nodes():
            x, y = self.pos[node]
            dist = math.sqrt((event.xdata - x)**2 + (event.ydata - y)**2)
            
            size_factor = self.node_sizes.get(node, 10) / 10
            threshold = 0.05 * size_factor
            
            if dist < threshold and dist < min_dist:
                min_dist = dist
                closest_node = node
        
        # We could add hover effect here like changing the cursor
        # For now, we'll just leave this as a placeholder


class MindMapWidget(QWidget):
    """Mind map widget that displays file relationships"""
    
    node_selected = pyqtSignal(str, str)  # node_id, node_type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mindMapWidget")
        
        # Set up the layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the matplotlib canvas
        self.canvas = MindMapCanvas(self)
        self.canvas.node_clicked.connect(self.handle_node_click)
        layout.addWidget(self.canvas)
        
        # Set background color
        self.setStyleSheet(f"background-color: {config.COLORS['mind_map_bg']};")
        
        # Initialize with a sample graph
        self.canvas.build_sample_graph()
    
    def handle_node_click(self, node_id, node_type):
        """Handle node click events from the canvas"""
        self.node_selected.emit(node_id, node_type)
    
    def update_with_files(self, files, tags=None, apps=None):
        """Update the mind map with actual file data"""
        if tags is None:
            tags = []
        if apps is None:
            apps = []
        
        self.canvas.build_graph_from_files(files, tags, apps)
    
    def highlight_node(self, node_id):
        """Highlight a specific node"""
        self.canvas.highlight_node(node_id)


class CustomMindMapWidget(QWidget):
    """Custom mind map widget that uses QPainter for better performance"""
    
    node_selected = pyqtSignal(str, str)  # node_id, node_type
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("customMindMapWidget")
        
        # Graph data
        self.nodes = {}  # id -> {pos, type, color, size}
        self.edges = {}  # (source, target) -> {color, width}
        
        # Interaction state
        self.highlighted_node = None
        self.animation_step = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        
        # Sample data
        self.create_sample_data()
        
        # Set background color
        self.setStyleSheet(f"background-color: {config.COLORS['mind_map_bg']};")
        
        # Start animation
        self.animation_timer.start(50)  # 50 ms interval
    
    def create_sample_data(self):
        """Create sample data for the mind map"""
        # File nodes
        files = [
            ('script.py', (0.2, 0.3)),
            ('document.docx', (-0.3, 0.1)),
            ('image.jpg', (0.1, -0.4)),
            ('presentation.pptx', (-0.5, -0.3)),
            ('data.csv', (0.4, 0.0))
        ]
        
        # App nodes
        apps = [
            ('VSCode', (0.6, 0.5)),
            ('Word', (-0.7, 0.3)),
            ('Photoshop', (0.3, -0.7)),
            ('PowerPoint', (-0.8, -0.5)),
            ('Excel', (0.8, -0.2))
        ]
        
        # Tag nodes
        tags = [
            ('Python', (0.4, 0.7)),
            ('Document', (-0.5, 0.6)),
            ('Image', (0.5, -0.5)),
            ('Presentation', (-0.9, -0.2)),
            ('Data', (0.7, 0.2)),
            ('ProjectX', (0.0, 0.0))
        ]
        
        # Add nodes
        for name, pos in files:
            self.nodes[name] = {
                'pos': pos,
                'type': 'file',
                'color': config.COLORS['files'],
                'size': config.MIND_MAP['node_size']['file']
            }
        
        for name, pos in apps:
            self.nodes[name] = {
                'pos': pos,
                'type': 'app',
                'color': config.COLORS['primary'],
                'size': config.MIND_MAP['node_size']['app']
            }
        
        for name, pos in tags:
            self.nodes[name] = {
                'pos': pos,
                'type': 'tag',
                'color': config.COLORS['tools'],
                'size': config.MIND_MAP['node_size']['tag']
            }
        
        # Add edges
        edges = [
            ('script.py', 'VSCode', 'dependency'),
            ('document.docx', 'Word', 'dependency'),
            ('image.jpg', 'Photoshop', 'dependency'),
            ('presentation.pptx', 'PowerPoint', 'dependency'),
            ('data.csv', 'Excel', 'dependency'),
            ('script.py', 'Python', 'tag'),
            ('document.docx', 'Document', 'tag'),
            ('image.jpg', 'Image', 'tag'),
            ('presentation.pptx', 'Presentation', 'tag'),
            ('data.csv', 'Data', 'tag'),
            ('script.py', 'ProjectX', 'project'),
            ('document.docx', 'ProjectX', 'project'),
            ('image.jpg', 'ProjectX', 'project')
        ]
        
        for source, target, edge_type in edges:
            if edge_type == 'dependency':
                color = config.COLORS['primary']
            elif edge_type == 'tag':
                color = config.COLORS['tools']
            elif edge_type == 'project':
                color = config.COLORS['cloud']
            else:
                color = config.COLORS['border']
                
            self.edges[(source, target)] = {
                'color': color,
                'width': config.MIND_MAP['edge_width']
            }
    
    def paintEvent(self, event):
        """Paint the mind map"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Transform coordinates from [-1,1] range to widget dimensions
        width = self.width()
        height = self.height()
        
        def transform_point(x, y):
            # Convert from [-1,1] to widget coordinates
            tx = width * (x + 1) / 2
            ty = height * (y + 1) / 2
            return tx, ty
        
        # Draw edges
        for (source, target), edge in self.edges.items():
            if source not in self.nodes or target not in self.nodes:
                continue
                
            x1, y1 = self.nodes[source]['pos']
            x2, y2 = self.nodes[target]['pos']
            
            tx1, ty1 = transform_point(x1, y1)
            tx2, ty2 = transform_point(x2, y2)
            
            # Set edge color and width
            color = QColor(edge['color'])
            
            # Make edges connected to highlighted node more prominent
            if self.highlighted_node in (source, target):
                color.setAlphaF(1.0)
                pen_width = edge['width'] + 0.5
            else:
                color.setAlphaF(0.7)
                pen_width = edge['width']
            
            pen = QPen(color)
            pen.setWidthF(pen_width)
            painter.setPen(pen)
            
            painter.drawLine(int(tx1), int(ty1), int(tx2), int(ty2))
        
        # Draw nodes
        for node_id, node in self.nodes.items():
            x, y = node['pos']
            tx, ty = transform_point(x, y)
            
            # Set node size
            base_size = node['size'] * 5  # Scale for visibility
            
            # Make highlighted node larger with animation
            if node_id == self.highlighted_node:
                size = base_size * (1.2 + 0.2 * math.sin(self.animation_step * 0.2))
                alpha = 1.0
                edge_color = QColor('white')
                edge_width = 2
            else:
                size = base_size
                alpha = 0.9
                edge_color = QColor(node['color'])
                edge_width = 1.5
            
            # Draw node circle
            color = QColor(node['color'])
            color.setAlphaF(alpha)
            
            painter.setBrush(QBrush(color))
            pen = QPen(edge_color)
            pen.setWidthF(edge_width)
            painter.setPen(pen)
            
            painter.drawEllipse(QPointF(tx, ty), size, size)
            
            # Draw text label
            painter.setPen(Qt.GlobalColor.white)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            # Create a path for the text to measure
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            
            text_width = painter.fontMetrics().horizontalAdvance(node_id)
            text_height = painter.fontMetrics().height()
            
            # Position text centered at node with a small offset
            text_x = tx - text_width / 2
            text_y = ty + size + text_height
            
            painter.drawText(int(text_x), int(text_y), node_id)
    
    def mousePressEvent(self, event):
        """Handle mouse click events"""
        # Find the closest node to the click
        closest_node = self.find_node_at(event.position().x(), event.position().y())
        
        if closest_node:
            self.highlight_node(closest_node)
            node_type = self.nodes[closest_node]['type']
            self.node_selected.emit(closest_node, node_type)
    
    def find_node_at(self, x, y):
        """Find the node at the given screen coordinates"""
        width = self.width()
        height = self.height()
        
        # Convert screen coordinates to [-1,1] range
        nx = 2 * x / width - 1
        ny = 2 * y / height - 1
        
        closest_node = None
        min_dist = float('inf')
        
        for node_id, node in self.nodes.items():
            node_x, node_y = node['pos']
            dist = math.sqrt((nx - node_x)**2 + (ny - node_y)**2)
            
            # Scale threshold by node size
            size_factor = node['size'] / 10
            threshold = 0.1 * size_factor
            
            if dist < threshold and dist < min_dist:
                min_dist = dist
                closest_node = node_id
        
        return closest_node
    
    def highlight_node(self, node_id):
        """Highlight a specific node"""
        self.highlighted_node = node_id
        self.animation_step = 0
        if not self.animation_timer.isActive():
            self.animation_timer.start(50)
        self.update()
    
    def update_animation(self):
        """Update animation state"""
        self.animation_step += 1
        if self.animation_step > 100:
            self.animation_step = 0
        
        # Only update if we have a highlighted node
        if self.highlighted_node:
            self.update()
    
    def update_with_files(self, files, tags=None, apps=None):
        """Update the mind map with actual file data"""
        # Clear existing data
        self.nodes = {}
        self.edges = {}
        
        # Initialize positions (we'd need a layout algorithm for real data)
        # For now, just place nodes in a circle
        node_count = len(files) + (len(tags) if tags else 0) + (len(apps) if apps else 0)
        current_node = 0
        
        # Add files
        for file in files:
            angle = 2 * math.pi * current_node / node_count
            radius = 0.7
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            self.nodes[file.name] = {
                'pos': (x, y),
                'type': 'file',
                'color': config.COLORS['files'],
                'size': config.MIND_MAP['node_size']['file']
            }
            current_node += 1
            
            # Connect to tags
            for tag in file.tags:
                if tag not in self.nodes:
                    # Place tag nodes in inner circle
                    tag_angle = 2 * math.pi * current_node / node_count
                    tag_radius = 0.4
                    tag_x = tag_radius * math.cos(tag_angle)
                    tag_y = tag_radius * math.sin(tag_angle)
                    
                    self.nodes[tag] = {
                        'pos': (tag_x, tag_y),
                        'type': 'tag',
                        'color': config.COLORS['tools'],
                        'size': config.MIND_MAP['node_size']['tag']
                    }
                    current_node += 1
                
                self.edges[(file.name, tag)] = {
                    'color': config.COLORS['tools'],
                    'width': config.MIND_MAP['edge_width']
                }
        
        # Add app connections if any
        if apps:
            for app_name in apps:
                # Place app nodes
                app_angle = 2 * math.pi * current_node / node_count
                app_radius = 0.6
                app_x = app_radius * math.cos(app_angle)
                app_y = app_radius * math.sin(app_angle)
                
                self.nodes[app_name] = {
                    'pos': (app_x, app_y),
                    'type': 'app',
                    'color': config.COLORS['primary'],
                    'size': config.MIND_MAP['node_size']['app']
                }
                current_node += 1
        
        # Trigger a repaint
        self.update()
