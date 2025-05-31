from PIL import Image, ImageDraw, ImageFont
import os

def create_default_teacher_image():
    # Create image with pink background
    img = Image.new('RGB', (200, 200), '#ff69b4')
    
    # Create drawing object
    draw = ImageDraw.Draw(img)
    
    # Draw a white circle in the center
    draw.ellipse([(25, 25), (175, 175)], fill='white')
    
    # Add text "Teacher" in the center
    try:
        # Try to use a system font
        font = ImageFont.truetype("Arial.ttf", 36)
    except:
        # Fallback to default font if Arial is not available
        font = ImageFont.load_default()
    
    # Calculate text position
    text = "Teacher"
    x = 50  # Fixed position
    y = 70  # Fixed position
    
    # Draw text
    draw.text((x, y), text, font=font, fill='#ff69b4')
    
    # Save image
    image_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'static', 'images', 'default-teacher.png'
    )
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    
    img.save(image_path)
    print(f'Default teacher image created at: {image_path}')

if __name__ == '__main__':
    create_default_teacher_image()
