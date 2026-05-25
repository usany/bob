import 'dotenv/config';
import OpenAI from 'openai';
import fs from 'node:fs';
import path from 'node:path';
import { GoogleGenAI } from "@google/genai";

const img = path.join(process.cwd(), 'downloads', 'c.png');
const openai = new OpenAI({
  baseURL: "https://integrate.api.nvidia.com/v1",
  apiKey: process.env.NVIDIA_NIM_API_KEY,
  // baseURL: 'https://openrouter.ai/api/v1',
  // apiKey: process.env.OPENROUTER_API_KEY,
});

const selection = "nvidia/nemotron-nano-12b-v2-vl"
// const selection = "moonshotai/kimi-k2.6"
// const selection = "google/gemma-4-26b-a4b-it:free"
const genai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY })

async function main() {
  try {
    const contents = [
      {
        inlineData: {
          mimeType: `image/png`,
          data: fs.readFileSync(img, "base64"),
        },
      },
      { text: "{'main': '만두라면, 치즈라면', 'side': None, 'price': 3000, 'calendar': None, 'time_category': ['아침', '저녁'], 'time_detail': {'아침': ['09:00', '10:00'], '저녁': ['17:30', '18:30']}, 'place': '청운관 학생식당', 'extra': None, 'non_pork': False}처럼 메뉴를 정리해주세요" }
    ]
    const response = await genai.models.generateContent({
      model: "gemini-3.5-flash",
      contents: contents,
    });
    console.log(response.text);

    // const completion = await openai.chat.completions.create({
    //   model: selection,
    //   messages: [
    //     {
    //       role: 'user',
    //       content: 'What is Deepseek in short?',
    //     },
    //   ],
    // });
    // console.log(completion.choices[0].message);

    const imagePath = img;
    const base64Image = fs.readFileSync(imagePath, "base64");
    try {

      const response = await openai.chat.completions.create({
        model: selection,
        messages: [
          {
            role: "user",
            content: [
              { type: "text", text: "파일 이미지에 쓰여 있는 대로만 음식 메뉴를 정확히 추출해 ## 푸른솔 교직원식당 * 푸른솔 소담(교직원식당) 11:00~14:00 * 푸른솔 교직원식당 11:00~14:00 * 푸른솔 비빔코너(교직원식당) 11:00~14:00 ## 푸른솔 학생식당 * 푸른솔 조식(학생식당) 08:00~09:30 * 푸른솔 중식 One Dish(학생식당) 11:00~14:30 세트/셀프바 * 푸른솔 중식 한소반(학생식당) 11:00~14:30 세트/셀프 * 푸른솔 TO-GO(One Dish) 08:30~16:00 * 푸른솔 셀프조리(One Dish) 08:30~16:00 토핑 * 푸른솔 TO-GO(무인판매) 월~목 14:30~16:00 로 메뉴를 정리해주세요" },
              {
                type: "image_url",
                image_url: { url: `data:image/jpeg;base64,${base64Image}` },
              },
            ],
          },
        ],
      });
      console.log(response.choices[0].message.content);
    } catch (err) {
      console.error(err.error.message);
    }

  } catch (err) {
    console.error(err)
  }
}
main()
export default main
