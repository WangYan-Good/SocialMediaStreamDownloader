document.addEventListener('DOMContentLoaded', function() {
  // 获取DOM元素
  const slider = document.getElementById('preferenceSlider');
  const sliderProgress = document.getElementById('sliderProgress');
  const percentageValue = document.getElementById('percentageValue');

  // 初始化进度条
  updateProgress(slider.value);

  // 滑动条值变化时更新显示
  slider.addEventListener('input', function() {
    updateProgress(this.value);
  });
});

// 更新进度条和百分比显示
function updateProgress(value) {
  sliderProgress.style.width = value + '%';
  percentageValue.textContent = value + '%';
  
  // 根据值改变颜色
  const hue = 120 * (value / 100); // 从红色(0)到绿色(120)
  const thumbColor = `hsl(${hue}, 60%, 50%)`;
  document.documentElement.style.setProperty('--thumb-color', thumbColor);
}