"""
ModelAI 主窗口界面
基于PyQt6，参考Claude界面风格设计
"""

import sys
import json
from typing import Optional, Dict, Any
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QLineEdit, QPushButton, QLabel, QFrame, QSplitter,
    QScrollArea, QGroupBox, QComboBox, QSpinBox, QCheckBox, QProgressBar,
    QStatusBar, QFileDialog, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor

from ..config.settings import settings, GenerationMode, ModelComplexity
from ..config.game_presets import GamePresets, GameType, ModelPurpose, QualityTier, Platform
from ..api.multi_ai_client import get_multi_ai_client, AIRequest
from ..agents.expert_panel import get_expert_panel, RequirementAnalysis


class ModelGenerationThread(QThread):
    """3D模型生成线程 - 使用专家组系统"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str) 
    analysis_completed = pyqtSignal(dict)  # 需求分析完成
    generation_completed = pyqtSignal(dict)
    generation_failed = pyqtSignal(str)
    
    def __init__(self, prompt: str, generation_config: Dict[str, Any]):
        super().__init__()
        self.prompt = prompt
        self.generation_config = generation_config
        self.expert_panel = get_expert_panel()
        self.client = get_multi_ai_client()
        
    async def _generate_model(self):
        """使用专家组系统的异步生成流程"""
        try:
            # 第一阶段：专家组需求分析 (30%进度)
            self.status_updated.emit("🧠 专家组会议中...")
            self.progress_updated.emit(5)
            
            # 调用专家组分析
            requirement_analysis = await self.expert_panel.analyze_requirement(
                self.prompt, 
                {"generation_config": self.generation_config}
            )
            
            self.progress_updated.emit(15)
            self.status_updated.emit("📋 制定执行计划...")
            
            # 获取分析摘要并发送给UI
            analysis_summary = await self.expert_panel.get_analysis_summary(requirement_analysis)
            analysis_data = {
                "analysis": requirement_analysis,
                "summary": analysis_summary,
                "required_agents": requirement_analysis.required_agents,
                "estimated_cost": requirement_analysis.estimated_cost,
                "complexity_level": requirement_analysis.complexity_level.value
            }
            
            self.analysis_completed.emit(analysis_data)
            
            self.progress_updated.emit(30)
            self.status_updated.emit("🤖 启动专业Agent团队...")
            
            # 第二阶段：动态调用Agent执行 (70%进度)
            agent_results = {}
            total_agents = len(requirement_analysis.required_agents)
            progress_step = 60 // max(total_agents, 1)  # 30%到90%的进度分配给Agent执行
            
            for i, agent_id in enumerate(requirement_analysis.required_agents):
                current_progress = 30 + (i * progress_step)
                self.progress_updated.emit(current_progress)
                
                # 根据Agent类型设置状态文本
                agent_status_map = {
                    "geometry_construction_agent": "🔺 构建几何结构",
                    "surface_detail_agent": "🎨 雕刻表面细节", 
                    "material_texture_agent": "🖼️ 设计材质纹理",
                    "functional_integration_agent": "🦴 集成功能系统",
                    "performance_optimization_agent": "⚡ 性能优化",
                    "quality_control_agent": "✅ 质量控制检查"
                }
                
                status_text = agent_status_map.get(agent_id, f"🤖 {agent_id}")
                self.status_updated.emit(status_text)
                
                # 调用Agent
                agent_result = await self._call_agent(
                    agent_id, 
                    self.prompt, 
                    requirement_analysis,
                    agent_results  # 传递之前Agent的结果
                )
                
                agent_results[agent_id] = agent_result
                
            self.progress_updated.emit(90)
            self.status_updated.emit("📊 整合最终结果...")
            
            # 第三阶段：整合最终结果
            final_result = {
                "requirement_analysis": requirement_analysis,
                "agent_results": agent_results,
                "generation_config": self.generation_config,
                "total_tokens": sum(result.get("tokens_used", 0) for result in agent_results.values()),
                "actual_cost": sum(result.get("cost", 0) for result in agent_results.values()),
                "agents_used": list(agent_results.keys())
            }
            
            self.progress_updated.emit(100)
            self.status_updated.emit("✅ 生成完成")
            self.generation_completed.emit(final_result)
            
        except Exception as e:
            self.generation_failed.emit(f"生成失败: {str(e)}")
    
    async def _call_agent(self, agent_id: str, prompt: str, analysis: RequirementAnalysis, previous_results: Dict) -> Dict:
        """调用单个Agent"""
        
        # 根据Agent类型构建专门的系统提示和请求
        agent_prompts = {
            "geometry_construction_agent": {
                "system": """你是几何构建专家，负责设计3D模型的基础几何结构和拓扑。
                
                专长领域：
                - 基础形状设计和比例控制
                - 顶点和面片的优化布局
                - 拓扑结构规划
                - 几何精度控制
                
                输出要求：详细的几何结构规格、顶点布局建议、拓扑优化方案。
                """,
                "content": f"""根据需求分析结果，设计几何结构：
                
                用户需求: {prompt}
                模型类型: {analysis.model_type}
                复杂度: {analysis.complexity_level.value} ({analysis.complexity_score}/10分)
                技术要求: {', '.join(analysis.technical_requirements)}
                特殊功能: {', '.join(analysis.special_features)}
                """
            },
            
            "material_texture_agent": {
                "system": """你是材质纹理专家，负责设计PBR材质和纹理贴图系统。
                
                专长领域：
                - PBR材质设计 (Albedo, Normal, Metallic, Roughness)
                - 纹理贴图规划和UV布局
                - 光照属性配置
                - Unity材质兼容性
                
                输出要求：材质规格、纹理需求、着色器配置、Unity材质球设置。
                """,
                "content": f"""为模型设计材质纹理系统：
                
                用户需求: {prompt}
                模型类型: {analysis.model_type}
                几何信息: {previous_results.get('geometry_construction_agent', {}).get('content', '待设计')[:200]}
                平台要求: {self.generation_config.get('platform_features', {}).get('hardware_level', 'mid')}
                """
            },
            
            "quality_control_agent": {
                "system": """你是质量控制专家，负责最终检查和Unity集成优化。
                
                专长领域：
                - 模型质量验证
                - 性能瓶颈识别
                - Unity导入优化
                - 兼容性检查
                
                输出要求：质量报告、优化建议、Unity导入配置、最终规格确认。
                """,
                "content": f"""对整个模型进行质量控制：
                
                用户需求: {prompt}
                几何结果: {previous_results.get('geometry_construction_agent', {}).get('content', '无')[:100]}
                材质结果: {previous_results.get('material_texture_agent', {}).get('content', '无')[:100]}
                目标平台: {self.generation_config.get('preset_summary', {}).get('platform', '通用')}
                性能目标: {self.generation_config.get('performance_target', '60fps')}
                """
            }
        }
        
        # 获取Agent配置，如果没有则使用通用配置
        agent_config = agent_prompts.get(agent_id, {
            "system": f"你是{agent_id}专家，请协助完成3D模型生成任务。",
            "content": f"处理需求: {prompt}"
        })
        
        # 发送请求
        request = AIRequest(
            messages=[{
                "role": "user",
                "content": agent_config["content"]
            }],
            system=agent_config["system"],
            max_tokens=1000,
            temperature=0.6
        )
        
        response = await self.client.send_message(request, agent_id)
        
        return {
            "agent_id": agent_id,
            "content": response.content,
            "tokens_used": response.usage.get("total_tokens", 0),
            "cost": response.usage.get("total_tokens", 0) * 0.00001,  # 粗略成本估算
            "processing_time": response.processing_time or 0
        }
    
    def run(self):
        """线程运行入口"""
        import asyncio
        asyncio.run(self._generate_model())


class MainWindow(QMainWindow):
    """ModelAI主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ModelAI {settings.app_version}")
        self.setGeometry(100, 100, settings.window_width, settings.window_height)
        
        # 应用Claude风格主题
        self.apply_claude_theme()
        
        # 初始化UI
        self.init_ui()
        
        # 初始化AI客户端
        self.client = get_multi_ai_client()
        
        # 生成线程
        self.generation_thread: Optional[ModelGenerationThread] = None
    
    def apply_claude_theme(self):
        """应用Claude风格主题"""
        if settings.enable_dark_mode:
            # 深色主题
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1a1a1a;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #1a1a1a;
                    color: #ffffff;
                    font-family: 'Segoe UI', sans-serif;
                }
                QTextEdit {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 14px;
                    line-height: 1.5;
                }
                QLineEdit {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #ff6b35;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #e85a2b;
                }
                QPushButton:pressed {
                    background-color: #d14d21;
                }
                QPushButton:disabled {
                    background-color: #404040;
                    color: #666666;
                }
                QFrame {
                    border: 1px solid #404040;
                    border-radius: 8px;
                }
                QComboBox, QSpinBox {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 6px;
                    padding: 6px;
                }
                QProgressBar {
                    border: 1px solid #404040;
                    border-radius: 6px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #ff6b35;
                    border-radius: 5px;
                }
            """)
    
    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        self.create_control_panel(splitter)
        
        # 右侧工作区
        self.create_work_area(splitter)
        
        # 设置分割比例
        splitter.setSizes([350, 1050])
        
        # 状态栏
        self.create_status_bar()
    
    def create_control_panel(self, parent):
        """创建左侧控制面板"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # 输入区域
        input_group = QGroupBox("模型需求输入")
        input_layout = QVBoxLayout(input_group)
        
        # 文本输入
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("描述你想要生成的3D模型...")
        self.prompt_input.setMaximumHeight(120)
        input_layout.addWidget(self.prompt_input)
        
        # 文件输入按钮
        file_buttons_layout = QHBoxLayout()
        self.image_button = QPushButton("添加图片")
        self.doc_button = QPushButton("添加文档")
        self.image_button.clicked.connect(self.add_image)
        self.doc_button.clicked.connect(self.add_document)
        file_buttons_layout.addWidget(self.image_button)
        file_buttons_layout.addWidget(self.doc_button)
        input_layout.addLayout(file_buttons_layout)
        
        control_layout.addWidget(input_group)
        
        # 智能预设选择
        settings_group = QGroupBox("🎯 智能预设 (为小白用户设计)")
        settings_layout = QVBoxLayout(settings_group)
        
        # 推荐预设
        recommend_layout = QVBoxLayout()
        recommend_layout.addWidget(QLabel("💡 推荐配置:"))
        self.recommend_combo = QComboBox()
        recommendations = GamePresets.get_recommended_presets()
        for rec in recommendations:
            self.recommend_combo.addItem(f"{rec['name']} - {rec['description']}")
        self.recommend_combo.currentTextChanged.connect(self.on_recommendation_changed)
        recommend_layout.addWidget(self.recommend_combo)
        settings_layout.addLayout(recommend_layout)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        settings_layout.addWidget(line)
        
        # 游戏类型
        game_type_layout = QHBoxLayout()
        game_type_layout.addWidget(QLabel("🎮 游戏类型:"))
        self.game_type_combo = QComboBox()
        for game_type in GameType:
            preset = GamePresets.GAME_TYPE_PRESETS[game_type]
            self.game_type_combo.addItem(preset.name)
        self.game_type_combo.setCurrentText("💻 PC独立游戏")
        self.game_type_combo.currentTextChanged.connect(self.update_all_parameters)
        game_type_layout.addWidget(self.game_type_combo)
        settings_layout.addLayout(game_type_layout)
        
        # 模型用途
        purpose_layout = QHBoxLayout()
        purpose_layout.addWidget(QLabel("🎭 模型用途:"))
        self.purpose_combo = QComboBox()
        for purpose in ModelPurpose:
            purpose_config = GamePresets.PURPOSE_PRESETS[purpose]
            self.purpose_combo.addItem(purpose_config["name"])
        self.purpose_combo.setCurrentText("⚔️ 道具物品")
        self.purpose_combo.currentTextChanged.connect(self.update_all_parameters)
        purpose_layout.addWidget(self.purpose_combo)
        settings_layout.addLayout(purpose_layout)
        
        # 质量档次
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("⭐ 质量档次:"))
        self.quality_combo = QComboBox()
        for quality in QualityTier:
            quality_config = GamePresets.QUALITY_PRESETS[quality]
            self.quality_combo.addItem(quality_config["name"])
        self.quality_combo.setCurrentText("✅ 发布标准")
        self.quality_combo.currentTextChanged.connect(self.update_all_parameters)
        quality_layout.addWidget(self.quality_combo)
        settings_layout.addLayout(quality_layout)
        
        # 目标平台
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("🌍 目标平台:"))
        self.platform_combo = QComboBox()
        self.platform_combo.addItem("通用平台 (自动适配)")  # 默认选项
        for platform in Platform:
            platform_config = GamePresets.PLATFORM_PRESETS[platform]
            self.platform_combo.addItem(platform_config.name)
        self.platform_combo.setCurrentText("通用平台 (自动适配)")
        self.platform_combo.currentTextChanged.connect(self.update_all_parameters)
        platform_layout.addWidget(self.platform_combo)
        settings_layout.addLayout(platform_layout)
        
        # 分割线  
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        settings_layout.addWidget(line2)
        
        # 可编辑参数面板
        params_group = QGroupBox("📊 生成参数 (可调整)")
        params_layout = QVBoxLayout(params_group)
        
        # 多边形数量
        poly_layout = QHBoxLayout()
        poly_layout.addWidget(QLabel("🔺 多边形数量:"))
        self.poly_spin = QSpinBox()
        self.poly_spin.setRange(100, 100000)
        self.poly_spin.setValue(10000)
        self.poly_spin.setSuffix(" 面")
        poly_layout.addWidget(self.poly_spin)
        params_layout.addLayout(poly_layout)
        
        # 纹理分辨率
        texture_layout = QHBoxLayout()
        texture_layout.addWidget(QLabel("🎨 纹理分辨率:"))
        self.texture_combo = QComboBox()
        self.texture_combo.addItems(["256x256", "512x512", "1024x1024", "2048x2048", "4096x4096"])
        self.texture_combo.setCurrentText("1024x1024")
        texture_layout.addWidget(self.texture_combo)
        params_layout.addLayout(texture_layout)
        
        # 性能目标
        performance_layout = QHBoxLayout()
        performance_layout.addWidget(QLabel("⚡ 性能目标:"))
        self.performance_label = QLabel("60fps on mid-range PC")
        self.performance_label.setStyleSheet("color: #ff6b35; font-weight: bold;")
        performance_layout.addWidget(self.performance_label)
        performance_layout.addStretch()
        params_layout.addLayout(performance_layout)
        
        # 内存限制
        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("💾 内存限制:"))
        self.memory_label = QLabel("2048 MB")
        self.memory_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        memory_layout.addWidget(self.memory_label)
        memory_layout.addStretch()
        params_layout.addLayout(memory_layout)
        
        # 多平台支持提示
        self.multi_platform_label = QLabel("")
        self.multi_platform_label.setStyleSheet("color: #2196F3; font-size: 12px; font-style: italic;")
        self.multi_platform_label.setWordWrap(True)
        params_layout.addWidget(self.multi_platform_label)
        
        # Unity功能选项
        unity_group = QGroupBox("🎮 Unity集成")
        unity_layout = QVBoxLayout(unity_group)
        
        # 基础功能
        basic_unity_layout = QHBoxLayout()
        self.lod_checkbox = QCheckBox("生成LOD层级")
        self.collider_checkbox = QCheckBox("生成碰撞体")
        self.material_checkbox = QCheckBox("生成材质球")
        basic_unity_layout.addWidget(self.lod_checkbox)
        basic_unity_layout.addWidget(self.collider_checkbox)
        basic_unity_layout.addWidget(self.material_checkbox)
        unity_layout.addLayout(basic_unity_layout)
        
        # 高级功能
        advanced_unity_layout = QHBoxLayout()
        self.pbr_checkbox = QCheckBox("PBR材质")
        self.animation_checkbox = QCheckBox("动画就绪")
        self.optimization_checkbox = QCheckBox("性能优化")
        advanced_unity_layout.addWidget(self.pbr_checkbox)
        advanced_unity_layout.addWidget(self.animation_checkbox)
        advanced_unity_layout.addWidget(self.optimization_checkbox)
        unity_layout.addLayout(advanced_unity_layout)
        
        params_layout.addWidget(unity_group)
        
        # AI Agent配置
        agent_group = QGroupBox("🤖 AI Agent配置")
        agent_layout = QVBoxLayout(agent_group)
        
        # 所需Agent显示和选择
        agent_selection_layout = QHBoxLayout()
        agent_selection_layout.addWidget(QLabel("所需Agent:"))
        self.agent_list_label = QLabel("geometry, material")
        self.agent_list_label.setStyleSheet("color: #cccccc; background-color: #2d2d2d; padding: 4px; border-radius: 3px;")
        agent_selection_layout.addWidget(self.agent_list_label)
        agent_layout.addLayout(agent_selection_layout)
        
        # 生成优先级
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("生成优先级:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["fastest", "balanced", "quality_first"])
        self.priority_combo.setCurrentText("balanced")
        priority_layout.addWidget(self.priority_combo)
        agent_layout.addLayout(priority_layout)
        
        params_layout.addWidget(agent_group)
        
        settings_layout.addWidget(params_group)
        
        # 更新初始参数
        self.update_all_parameters()
        
        control_layout.addWidget(settings_group)
        
        # 生成按钮
        self.generate_button = QPushButton("生成3D模型")
        self.generate_button.clicked.connect(self.start_generation)
        control_layout.addWidget(self.generate_button)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        # 弹性空间
        control_layout.addStretch()
        
        parent.addWidget(control_widget)
    
    def create_work_area(self, parent):
        """创建右侧工作区"""
        work_widget = QWidget()
        work_layout = QVBoxLayout(work_widget)
        
        # 标签页
        self.tab_widget = QTabWidget()
        
        # 对话记录标签页
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setPlaceholderText("AI助手的分析和建议将显示在这里...")
        self.tab_widget.addTab(self.chat_area, "AI对话")
        
        # 技术规格标签页
        self.specs_area = QTextEdit()
        self.specs_area.setReadOnly(True)
        self.specs_area.setPlaceholderText("生成的技术规格将显示在这里...")
        self.tab_widget.addTab(self.specs_area, "技术规格")
        
        # 预览标签页
        self.preview_area = QLabel()
        self.preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_area.setText("3D模型预览\n(功能开发中)")
        self.preview_area.setStyleSheet("color: #666666; font-size: 16px;")
        self.tab_widget.addTab(self.preview_area, "3D预览")
        
        work_layout.addWidget(self.tab_widget)
        
        parent.addWidget(work_widget)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # AI服务状态
        self.ai_status_label = QLabel("AI服务: 未连接")
        self.status_bar.addWidget(self.ai_status_label)
        
        # 更新AI状态
        self.update_ai_status()
    
    def update_ai_status(self):
        """更新AI服务状态"""
        try:
            available_services = self.client.get_available_services()
            service_names = [s.value for s in available_services]
            self.ai_status_label.setText(f"AI服务: {', '.join(service_names)}")
        except:
            self.ai_status_label.setText("AI服务: 连接失败")
    
    def add_image(self):
        """添加图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.append_to_chat(f"📷 已添加图片: {Path(file_path).name}")
    
    def add_document(self):
        """添加文档"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文档", "",
            "文档文件 (*.pdf *.txt *.doc *.docx)"
        )
        if file_path:
            self.append_to_chat(f"📄 已添加文档: {Path(file_path).name}")
    
    def get_generation_config(self) -> Dict[str, Any]:
        """获取生成配置"""
        # 获取当前选择的预设
        game_type = self.get_selected_game_type()
        purpose = self.get_selected_purpose()
        quality = self.get_selected_quality()
        platform = self.get_selected_platform()
        
        # 获取智能预设配置
        preset_config = GamePresets.get_combined_config(game_type, purpose, quality, platform)
        
        # 使用当前UI中的实际参数值（用户可能已修改）
        if hasattr(self, 'poly_spin'):
            preset_config["poly_count"] = self.poly_spin.value()
            preset_config["texture_size"] = int(self.texture_combo.currentText().split('x')[0])
            preset_config["generation_priority"] = self.priority_combo.currentText()
            
            # Unity功能从UI读取
            preset_config["unity_features"].update({
                "generate_lods": self.lod_checkbox.isChecked(),
                "generate_colliders": self.collider_checkbox.isChecked(),
                "generate_materials": self.material_checkbox.isChecked(),
                "pbr_materials": self.pbr_checkbox.isChecked() if hasattr(self, 'pbr_checkbox') else False,
                "animation_ready": self.animation_checkbox.isChecked() if hasattr(self, 'animation_checkbox') else False,
                "performance_optimized": self.optimization_checkbox.isChecked() if hasattr(self, 'optimization_checkbox') else False
            })
        
        return preset_config
    
    def get_selected_game_type(self) -> GameType:
        """获取选中的游戏类型"""
        type_map = {
            "📱 手机游戏": GameType.MOBILE,
            "💻 PC独立游戏": GameType.INDIE_PC,
            "🏆 PC大型游戏": GameType.AAA_PC,
            "🥽 VR游戏": GameType.VR,
            "🎮 复古像素": GameType.RETRO,
            "🕹️ 主机游戏": GameType.CONSOLE
        }
        return type_map[self.game_type_combo.currentText()]
    
    def get_selected_purpose(self) -> ModelPurpose:
        """获取选中的模型用途"""
        purpose_map = {
            "👤 主角模型": ModelPurpose.MAIN_CHARACTER,
            "🤖 NPC角色": ModelPurpose.NPC,
            "🏠 建筑场景": ModelPurpose.ARCHITECTURE,
            "⚔️ 道具物品": ModelPurpose.PROPS,
            "⚔️ 武器装备": ModelPurpose.WEAPONS,
            "🚗 载具车辆": ModelPurpose.VEHICLES,
            "🌲 环境装饰": ModelPurpose.ENVIRONMENT
        }
        return purpose_map[self.purpose_combo.currentText()]
    
    def get_selected_quality(self) -> QualityTier:
        """获取选中的质量档次"""
        quality_map = {
            "⚡ 快速原型": QualityTier.PROTOTYPE,
            "✅ 发布标准": QualityTier.PRODUCTION,
            "💎 展示精品": QualityTier.SHOWCASE
        }
        return quality_map[self.quality_combo.currentText()]
    
    def get_selected_platform(self) -> Platform:
        """获取选中的目标平台"""
        platform_text = self.platform_combo.currentText()
        
        # 如果选择的是通用平台，返回None
        if platform_text == "通用平台 (自动适配)":
            return None
            
        # 构建平台映射
        platform_map = {}
        for platform in Platform:
            platform_config = GamePresets.PLATFORM_PRESETS[platform]
            platform_map[platform_config.name] = platform
            
        return platform_map.get(platform_text)
    
    def update_all_parameters(self):
        """更新所有参数显示和控件值"""
        try:
            # 获取预设配置（不包括UI修改）
            game_type = self.get_selected_game_type()
            purpose = self.get_selected_purpose()
            quality = self.get_selected_quality()
            platform = self.get_selected_platform()
            preset_config = GamePresets.get_combined_config(game_type, purpose, quality, platform)
            
            # 更新技术参数控件
            if hasattr(self, 'poly_spin'):
                self.poly_spin.setValue(preset_config['poly_count'])
                self.texture_combo.setCurrentText(f"{preset_config['texture_size']}x{preset_config['texture_size']}")
                
                # 更新性能目标显示
                if hasattr(self, 'performance_label'):
                    self.performance_label.setText(preset_config['performance_target'])
                
                # 更新内存限制显示
                if hasattr(self, 'memory_label'):
                    memory_limit = preset_config.get('memory_limit', 2048)
                    self.memory_label.setText(f"{memory_limit} MB")
                
                # 更新多平台支持提示
                if hasattr(self, 'multi_platform_label'):
                    platform_features = preset_config.get('platform_features', {})
                    multi_quality = platform_features.get('multi_quality_support', False)
                    hardware_level = platform_features.get('hardware_level', 'mid')
                    
                    if multi_quality:
                        self.multi_platform_label.setText(
                            f"🌍 多平台支持: 将生成多个质量版本适配不同设备 | 硬件级别: {hardware_level.upper()}"
                        )
                    elif platform:
                        self.multi_platform_label.setText(
                            f"🎯 专为 {preset_config['preset_summary'].get('platform', '通用')} 优化 | 硬件级别: {hardware_level.upper()}"
                        )
                    else:
                        self.multi_platform_label.setText("🌍 通用配置，适配多种平台")
                
                # 更新Unity功能选项
                unity_features = preset_config.get('unity_features', {})
                self.lod_checkbox.setChecked(unity_features.get('generate_lods', False))
                self.collider_checkbox.setChecked(unity_features.get('generate_colliders', False))
                self.material_checkbox.setChecked(unity_features.get('generate_materials', False))
                
                if hasattr(self, 'pbr_checkbox'):
                    self.pbr_checkbox.setChecked(unity_features.get('pbr_materials', False))
                if hasattr(self, 'animation_checkbox'):
                    self.animation_checkbox.setChecked(unity_features.get('animation_ready', False))
                if hasattr(self, 'optimization_checkbox'):
                    self.optimization_checkbox.setChecked(unity_features.get('performance_optimized', False))
                
                # 更新Agent配置显示
                if hasattr(self, 'agent_list_label'):
                    agent_names = [agent.replace('_agent', '') for agent in preset_config['required_agents']]
                    self.agent_list_label.setText(', '.join(agent_names))
                
                if hasattr(self, 'priority_combo'):
                    priority = preset_config.get('generation_priority', 'balanced')
                    self.priority_combo.setCurrentText(priority)
                
        except Exception as e:
            print(f"参数更新失败: {e}")
    
    def on_recommendation_changed(self):
        """推荐配置改变处理"""
        try:
            recommendations = GamePresets.get_recommended_presets()
            index = self.recommend_combo.currentIndex()
            if 0 <= index < len(recommendations):
                game_type, purpose, quality = recommendations[index]["config"]
                
                # 更新选择器
                game_preset = GamePresets.GAME_TYPE_PRESETS[game_type]
                purpose_config = GamePresets.PURPOSE_PRESETS[purpose]
                quality_config = GamePresets.QUALITY_PRESETS[quality]
                
                self.game_type_combo.setCurrentText(game_preset.name)
                self.purpose_combo.setCurrentText(purpose_config["name"])
                self.quality_combo.setCurrentText(quality_config["name"])
                
                # 更新参数
                self.update_all_parameters()
                
        except Exception as e:
            print(f"推荐配置更新失败: {e}")
    
    def start_generation(self):
        """开始生成模型"""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "警告", "请输入模型描述")
            return
        
        # 准备生成
        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 清空显示区域
        self.chat_area.clear()
        self.specs_area.clear()
        
        # 显示开始信息和预设
        config = self.get_generation_config()
        summary = config["preset_summary"]
        
        self.append_to_chat(f"🚀 开始生成: {prompt}")
        self.append_to_chat(f"🎮 游戏类型: {summary['game_type']}")
        self.append_to_chat(f"🎭 模型用途: {summary['model_purpose']}")
        self.append_to_chat(f"⭐ 质量档次: {summary['quality_tier']}")
        self.append_to_chat(f"📊 技术参数: {config['poly_count']:,}面, {config['texture_size']}×{config['texture_size']}纹理")
        
        # 启动生成线程
        self.generation_thread = ModelGenerationThread(prompt, self.get_generation_config())
        self.generation_thread.progress_updated.connect(self.progress_bar.setValue)
        self.generation_thread.status_updated.connect(self.status_bar.showMessage)
        self.generation_thread.analysis_completed.connect(self.on_analysis_completed)  # 新增
        self.generation_thread.generation_completed.connect(self.on_generation_completed)
        self.generation_thread.generation_failed.connect(self.on_generation_failed)
        self.generation_thread.start()
    
    def append_to_chat(self, message: str):
        """添加消息到对话区"""
        self.chat_area.append(message)
        self.chat_area.append("")  # 空行
    
    def on_analysis_completed(self, analysis_data: Dict[str, Any]):
        """需求分析完成处理"""
        analysis = analysis_data["analysis"]
        summary = analysis_data["summary"]
        
        self.append_to_chat("🧠 专家组分析完成！")
        self.append_to_chat(summary)
        self.append_to_chat(f"📋 将调用 {len(analysis.required_agents)} 个专业Agent：")
        
        # 显示Agent列表
        agent_names_map = {
            "geometry_construction_agent": "🔺 几何构建专家",
            "surface_detail_agent": "🎨 表面细节专家", 
            "material_texture_agent": "🖼️ 材质纹理专家",
            "functional_integration_agent": "🦴 功能集成专家",
            "performance_optimization_agent": "⚡ 性能优化专家",
            "quality_control_agent": "✅ 质量控制专家"
        }
        
        for agent_id in analysis.required_agents:
            agent_name = agent_names_map.get(agent_id, agent_id)
            self.append_to_chat(f"  • {agent_name}")
        
        if analysis.potential_challenges:
            self.append_to_chat(f"⚠️ 注意事项: {', '.join(analysis.potential_challenges[:2])}")
            
        self.append_to_chat("🚀 开始执行建模任务...")
    
    def on_generation_completed(self, result: Dict[str, Any]):
        """生成完成处理 - 支持新的专家组结果格式"""
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # 获取结果数据
        requirement_analysis = result.get('requirement_analysis')
        agent_results = result.get('agent_results', {})
        agents_used = result.get('agents_used', [])
        
        # 显示完成信息
        self.append_to_chat("🎉 所有Agent工作完成!")
        self.append_to_chat(f"🤖 共调用了 {len(agents_used)} 个专业Agent")
        self.append_to_chat(f"📊 总Token消耗: {result.get('total_tokens', 0):,}")
        self.append_to_chat(f"💰 实际成本: ${result.get('actual_cost', 0):.3f}")
        
        # 显示各Agent工作结果摘要
        agent_names_map = {
            "geometry_construction_agent": "🔺 几何构建结果",
            "surface_detail_agent": "🎨 表面细节结果", 
            "material_texture_agent": "🖼️ 材质纹理结果",
            "functional_integration_agent": "🦴 功能集成结果",
            "performance_optimization_agent": "⚡ 性能优化结果",
            "quality_control_agent": "✅ 质量控制结果"
        }
        
        for agent_id in agents_used:
            agent_result = agent_results.get(agent_id, {})
            agent_name = agent_names_map.get(agent_id, agent_id)
            
            self.append_to_chat(f"{agent_name}:")
            content = agent_result.get('content', '')
            # 显示前200字符作为摘要
            self.append_to_chat(content[:200] + ("..." if len(content) > 200 else ""))
        
        # 更新技术规格页 - 新格式
        self._update_specs_with_expert_results(result)
        
        # 切换到规格页
        self.tab_widget.setCurrentIndex(1)
    
    def _update_specs_with_expert_results(self, result: Dict[str, Any]):
        """使用专家组结果更新技术规格页"""
        requirement_analysis = result.get('requirement_analysis')
        agent_results = result.get('agent_results', {})
        config = result.get('generation_config', {})
        summary = config.get('preset_summary', {})
        
        specs_content = f"""
🎯 专家组分析总结:
===================
🎮 游戏类型: {summary.get('game_type', '未知')}
🎭 模型用途: {summary.get('model_purpose', '未知')}
⭐ 质量档次: {summary.get('quality_tier', '未知')}
🌍 目标平台: {summary.get('platform', '通用')}
📝 配置说明: {summary.get('description', '')}

📊 智能分析结果:
===================
• 模型类型: {requirement_analysis.model_type if requirement_analysis else '未知'}
• 复杂度级别: {requirement_analysis.complexity_level.value.upper() if requirement_analysis else '未知'} ({requirement_analysis.complexity_score if requirement_analysis else 0}/10分)
• 复杂度因素: {', '.join(requirement_analysis.complexity_factors) if requirement_analysis and requirement_analysis.complexity_factors else '无'}
• 技术要求: {', '.join(requirement_analysis.technical_requirements) if requirement_analysis and requirement_analysis.technical_requirements else '无'}
• 特殊功能: {', '.join(requirement_analysis.special_features) if requirement_analysis and requirement_analysis.special_features else '无'}

💰 成本分析:
===================
• 预计成本: ${requirement_analysis.estimated_cost if requirement_analysis else 0:.3f}
• 实际成本: ${result.get('actual_cost', 0):.3f}
• 预计Token: {requirement_analysis.estimated_tokens if requirement_analysis else 0:,}
• 实际Token: {result.get('total_tokens', 0):,}
• 成功概率: {requirement_analysis.success_probability:.0%} if requirement_analysis else '未知'

🤖 Agent执行结果:
===================
"""
        
        # 添加各Agent的详细结果
        agent_names_map = {
            "geometry_construction_agent": "🔺 几何构建专家",
            "surface_detail_agent": "🎨 表面细节专家", 
            "material_texture_agent": "🖼️ 材质纹理专家",
            "functional_integration_agent": "🦴 功能集成专家",
            "performance_optimization_agent": "⚡ 性能优化专家",
            "quality_control_agent": "✅ 质量控制专家"
        }
        
        for agent_id, agent_result in agent_results.items():
            agent_name = agent_names_map.get(agent_id, agent_id)
            specs_content += f"""
{agent_name}:
-------------------
Token消耗: {agent_result.get('tokens_used', 0)}
处理时间: {agent_result.get('processing_time', 0):.2f}s
成本: ${agent_result.get('cost', 0):.4f}

工作结果:
{agent_result.get('content', '无结果')}

"""
        
        # 添加Unity集成配置
        specs_content += f"""
⚙️ Unity集成配置:
===================
{json.dumps(config.get('unity_features', {}), indent=2, ensure_ascii=False)}

🌍 平台优化特性:
===================
{json.dumps(config.get('platform_features', {}), indent=2, ensure_ascii=False)}
        """
        
        self.specs_area.setPlainText(specs_content)
    
    def on_generation_failed(self, error: str):
        """生成失败处理"""
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.append_to_chat(f"❌ 生成失败: {error}")
        QMessageBox.critical(self, "生成失败", f"模型生成过程中出现错误:\n{error}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("ModelAI")
    app.setApplicationVersion(settings.app_version)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())