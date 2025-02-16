'use client'

import { useState, useEffect, useRef } from 'react'
import TypeWriter from '@/components/TypeWriter'
import AnimatedResponse from '@/components/AnimatedResponse'

// Define our responses
const base_url = "https://4017-2001-5a8-450b-4900-9555-6b3a-f17f-92e.ngrok-free.app"
const responses = [
  {
    header: "Deciding your model",
    content: ""
  },
  {
    header: "Scraping data for your model",
    content: ""
  },
  {
    header: "Creating your model",
    content: ""
  },
  {
    header: "Deploying your model",
    content: ""
  }
];

export default function Home() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<string[]>([])
  const [isMinimized, setIsMinimized] = useState(false)
  const [messageVisible, setMessageVisible] = useState<boolean[]>([])
  const [hideInput, setHideInput] = useState(false)
  const [currentResponseIndex, setCurrentResponseIndex] = useState(-1)
  const [responseVisible, setResponseVisible] = useState<boolean[]>([false, false, false, false])
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [])
  

  useEffect(() => {
    if (messages.length > messageVisible.length) {
      setTimeout(() => {
        setMessageVisible([...messageVisible, true])
      }, 100)
    }
  }, [messages])

  const resetToInitialState = () => {
    setInput('')
    setMessages([])
    setIsMinimized(false)
    setMessageVisible([])
    setHideInput(false)
    setCurrentResponseIndex(-1)
    // Focus the input after a short delay to ensure DOM is ready
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus()
      }
    }, 100)
  }

  const handleKeyPress = async (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (input.trim()) {
        setMessages([...messages, input])
        setInput('')
        setIsMinimized(true)
        setTimeout(() => {
          setHideInput(true)
        }, 200)
        await requestMlModel(input.trim()) //added this await here 
      }
    }
  }

  const requestMlModel = async (prompt: string) => {
    // POST request to /request_model/ that will send request: prompt
    // Receives back the prompt that is generated as the search prompt
    console.log("Sending request with prompt:", prompt);
    const response = await fetch(base_url + '/request_model/?request=' + prompt, {
      method: 'POST',
    })
    let response_json = JSON.parse(await response.json())
    console.log("Response json:", response_json)
    responses[0].content = response_json.webscraping_prompt
    setCurrentResponseIndex(0); // Set this first to ensure component is visible
    setResponseVisible(prev => {
      const newVisible = [...prev];
      newVisible[0] = true;
      return newVisible;
    })
    console.log("Received search prompt:", responses[0].content)
    
    // Wait for the first animation to complete before polling
    // Animation takes ~30ms per 2 chars + 1000ms wait + 500ms collapse = ~2-3s total
    const animationTime = (responses[0].content.length / 2) * 30 + 1500;
    await new Promise(resolve => setTimeout(resolve, animationTime));
    
    await pollStage()
  }
  type StageResponse = {
    stage: keyof typeof stages
    summary: string
  }
  //write a hashmap with stage as key and then index of response as value
  const stages = {
    "parsing": 0,
    "scraping": 1,
    "finetuning": 2,
    "deploying": 3
  } as const;

  //now based on what the stage is, in pollstage we should manipulate that and set it to whatever the corresponding index is
  const pollStage = async () => {
    console.log("waiting 5 seconds")
    return new Promise((resolve) => {
      setTimeout(async () => {
        console.log("waited 5 seconds, fetching")
        const response = await fetch(base_url + "/request_stage/", {
          method: 'GET',
        })
        let response_json = await response.json() as StageResponse
        let stage = response_json.stage
        let summary = response_json.summary

        responses[stages[stage]].content = summary
        console.log("Responses: " + responses[0].content + responses[1].content + responses[2].content + responses[3].content)
        
        // First set visibility to false to trigger re-render
        setResponseVisible(prev => {
          const newVisible = [...prev];
          newVisible[stages[stage]] = false;
          console.log("Response visible: " + newVisible);
          return newVisible;
        })

        // Then set it back to true after a delay
        setTimeout(() => {
          setResponseVisible(prev => {
            const newVisible = [...prev];
            newVisible[stages[stage]] = true;
            console.log("Response visible: " + newVisible);
            return newVisible;
          })
        }, 500)

        setCurrentResponseIndex(prev => stages[stage])
        resolve(response_json)
      }, 5000)
    })
  }

  const handleResponseComplete = () => {
    // Move to next response after a small delay
    setTimeout(async () => {
      const result = await pollStage()
      if (!result) {
        //if our polling is resolving to null then we can try again
        await pollStage()
      }
    }, 500)
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const textarea = e.target
    setInput(textarea.value)
    textarea.style.height = 'auto'
    textarea.style.height = `${textarea.scrollHeight}px`
  }

  return (
    <main className="min-h-screen w-full bg-white p-4">
      <div className="w-full h-[96vh] bg-black relative overflow-hidden">
        {/* Title */}
        <button 
          onClick={resetToInitialState}
          className={`absolute transition-all duration-800 ease-out origin-top-left ${
            isMinimized 
              ? 'top-6 left-6 scale-[0.25]' 
              : 'top-[6%] left-1/2 -translate-x-1/2'
          }`}
        >
          <TypeWriter 
            text="blacksmith"
            className="text-white text-[7rem] leading-none tracking-tight whitespace-nowrap"
            delay={150}
          />
        </button>
        
        {/* Messages */}
        <div className="absolute top-[10%] left-0 right-0 flex flex-col items-center px-8">
          {messages.map((message, index) => (
            <div 
              key={index}
              className={`message-container text-white/90 text-2xl mb-6 max-w-[600px] w-full break-words whitespace-pre-wrap text-center ${
                messageVisible[index] ? 'message-visible' : ''
              }`}
            >
              {message.split('\n').map((line, i) => (
                <div key={i} className="mb-1 break-words text-center">
                  {line || '\u00A0'}
                </div>
              ))}
            </div>
          ))}
          
          {/* Animated Responses */}
          <div className="w-full max-w-[600px] mt-8 space-y-6">
            {responses.map((response, index) => ( //keep track of the stage 
              <AnimatedResponse //4 divs empty content - based on content, loop that pulls request state when animation is finsihed
                key={index}
                header={response.header}
                text={response.content}
                isVisible={currentResponseIndex >= index && responseVisible[index]}
                onComplete={handleResponseComplete}
              />
            ))}
          </div>
        </div>
        
        {/* Chat input */}
        <div className={`input-container absolute left-1/2 transform -translate-x-1/2 ${
          isMinimized ? 'bottom-8' : 'top-1/2 -translate-y-1/2'
        } ${hideInput ? 'opacity-0 pointer-events-none' : ''}`}>
          <div className="relative">
            <div className="absolute inset-0 bg-black" />
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInput}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              rows={1}
              className="relative w-[500px] p-4 bg-white/10 text-white border border-white/20 focus:outline-none focus:border-white/40 transition-colors resize-none overflow-hidden min-h-[56px] max-h-[200px] break-words whitespace-pre-wrap"
              style={{ height: 'auto' }}
            />
          </div>
        </div>
      </div>
    </main>
  )
}
