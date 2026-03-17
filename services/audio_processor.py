#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频处理服务
处理MP3文件，进行语音分离
"""

import os
import logging
from pydub import AudioSegment

logger = logging.getLogger(__name__)

PYANNOTE_AVAILABLE = False
Pipeline = None

try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
    logger.info("pyannote.audio 已成功导入")
except ImportError as e:
    logger.warning(f"pyannote.audio 导入失败: {e}，将使用模拟模式")
    PYANNOTE_AVAILABLE = False


class AudioProcessor:
    """音频处理器类"""
    
    DEFAULT_MODEL = "pyannote/speaker-diarization-3.1"
    
    def __init__(self, filepath, use_pyannote=True):
        """
        初始化音频处理器
        
        Args:
            filepath: 音频文件路径
            use_pyannote: 是否使用 pyannote 进行真实分离，默认为 True
        """
        self.filepath = filepath
        self.use_pyannote = use_pyannote and PYANNOTE_AVAILABLE
        self._pipeline = None
        self._model_loaded = False
        
        if self.use_pyannote:
            logger.info(f"AudioProcessor 初始化: 启用 pyannote 模式，文件: {filepath}")
        else:
            logger.info(f"AudioProcessor 初始化: 使用模拟模式，文件: {filepath}")
    
    def load_model(self, model_name=None, use_auth_token=None):
        """
        加载 pyannote 模型
        
        Args:
            model_name: 模型名称，默认使用 pyannote/speaker-diarization-3.1
            use_auth_token: HuggingFace token，如未提供则从环境变量获取
            
        Returns:
            bool: 模型是否加载成功
        """
        if not PYANNOTE_AVAILABLE:
            logger.warning("pyannote.audio 不可用，无法加载模型")
            return False
        
        if self._model_loaded and self._pipeline is not None:
            logger.debug("模型已加载，跳过重复加载")
            return True
        
        model_name = model_name or self.DEFAULT_MODEL
        
        if use_auth_token is None:
            use_auth_token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")
        
        try:
            logger.info(f"正在加载 pyannote 模型: {model_name}")
            self._pipeline = Pipeline.from_pretrained(
                model_name,
                use_auth_token=use_auth_token
            )
            self._model_loaded = True
            logger.info(f"pyannote 模型加载成功: {model_name}")
            return True
        except Exception as e:
            logger.error(f"pyannote 模型加载失败: {e}")
            self._pipeline = None
            self._model_loaded = False
            return False
    
    def separate_speakers(self, num_speakers=2):
        """
        分离说话人的语音
        
        Args:
            num_speakers: 预期说话人数量，默认为 2
            
        Returns:
            dict: 包含每个说话人的音频片段信息
                - speaker1/speaker2: 原始文件路径（兼容旧接口）
                - segments: 每个说话人的时间段列表
        """
        if self.use_pyannote:
            return self._separate_with_pyannote(num_speakers)
        else:
            return self._separate_mock()
    
    def _separate_with_pyannote(self, num_speakers=2):
        """
        使用 pyannote 进行真实的说话人分离
        
        Args:
            num_speakers: 预期说话人数量
            
        Returns:
            dict: 包含说话人分离结果
        """
        if not self._model_loaded:
            if not self.load_model():
                logger.warning("模型加载失败，回退到模拟模式")
                return self._separate_mock()
        
        try:
            logger.info(f"开始处理音频文件: {self.filepath}")
            
            diarization = self._pipeline(
                self.filepath,
                num_speakers=num_speakers
            )
            
            speaker_segments = {}
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                if speaker not in speaker_segments:
                    speaker_segments[speaker] = []
                
                segment_info = {
                    'start': round(turn.start, 3),
                    'end': round(turn.end, 3),
                    'duration': round(turn.end - turn.start, 3)
                }
                speaker_segments[speaker].append(segment_info)
            
            speaker_list = list(speaker_segments.keys())
            result = {
                'speaker1': self.filepath,
                'speaker2': self.filepath,
                'segments': {},
                'total_speakers': len(speaker_list),
                'model_used': self.DEFAULT_MODEL
            }
            
            for i, speaker in enumerate(speaker_list[:num_speakers]):
                speaker_key = f'speaker{i + 1}'
                result['segments'][speaker_key] = speaker_segments[speaker]
                logger.info(f"{speaker_key}: 发现 {len(speaker_segments[speaker])} 个音频片段")
            
            logger.info(f"说话人分离完成，共发现 {len(speaker_list)} 个说话人")
            return result
            
        except Exception as e:
            logger.error(f"pyannote 处理过程中出错: {e}，回退到模拟模式")
            return self._separate_mock()
    
    def _separate_mock(self):
        """
        模拟说话人分离（降级模式）
        
        Returns:
            dict: 模拟的分离结果
        """
        logger.info("使用模拟模式返回结果")
        
        return {
            'speaker1': self.filepath,
            'speaker2': self.filepath,
            'segments': {
                'speaker1': [
                    {'start': 0.0, 'end': 30.0, 'duration': 30.0},
                    {'start': 60.0, 'end': 90.0, 'duration': 30.0}
                ],
                'speaker2': [
                    {'start': 30.0, 'end': 60.0, 'duration': 30.0},
                    {'start': 90.0, 'end': 120.0, 'duration': 30.0}
                ]
            },
            'total_speakers': 2,
            'model_used': 'mock'
        }
    
    def get_audio_info(self):
        """
        获取音频信息
        
        Returns:
            dict: 音频信息，包含真实时长（秒）
        """
        file_size = os.path.getsize(self.filepath)
        
        try:
            # 使用pydub获取真实音频时长
            audio = AudioSegment.from_mp3(self.filepath)
            duration = len(audio) / 1000  # 转换为秒
            channels = audio.channels
            sample_rate = audio.frame_rate
            sample_width = audio.sample_width * 8  # 转换为位
            
            logger.info(f"音频信息: 时长={duration:.2f}秒, 声道={channels}, 采样率={sample_rate}")
            
            return {
                'duration': duration,
                'channels': channels,
                'sample_rate': sample_rate,
                'sample_width': sample_width,
                'file_size': file_size
            }
        except Exception as e:
            logger.error(f"获取音频信息失败: {e}")
            # 降级处理：返回默认值
            return {
                'duration': 0,
                'channels': 2,
                'sample_rate': 44100,
                'sample_width': 16,
                'file_size': file_size
            }
    
    @classmethod
    def is_pyannote_available(cls):
        """
        检查 pyannote.audio 是否可用
        
        Returns:
            bool: pyannote.audio 是否可用
        """
        return PYANNOTE_AVAILABLE
