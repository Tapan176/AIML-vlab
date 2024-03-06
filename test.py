from openai import OpenAI

client = OpenAI(
  api_key='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',
)
response = client.images.create_variation(
  image=open("C:\\Users\\ZTI\\Downloads\\Slide0-773bd114.png", "rb"),
  n=2,
  size="1024x1024"
)

image_url = response.data[0].url