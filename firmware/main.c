
/** Name: main.c
 * Author: planasb (kesrut@riseup.net)
 * License: GPLv2
 */

#include <stdio.h>
#include <string.h>
#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>
#include "main.h"

#define DEBUG 1
//#define ADC_DEBUG 1
#define FOSC 16000000UL
#define BAUD 38400
#define BAUDRATE ((FOSC)/(BAUD*16UL)-1)
#define QUEUE_SIZE 128 
#define true 1
#define false 0

#define START 0
#define STOP 1
#define RUNNING 2
#define PACKET_START 1
#define PACKET_SIZE 2
#define PACKET_DATA 3
#define PACKET_END 4
#define PACKET_START_MAGIC 0x5C
#define PACKET_END_MAGIC 0xC5
#define START_MAGIC 'a'
#define STOP_MAGIC 'b' 

unsigned short NUMBER_VALUES = 1024 ; 
volatile unsigned short adc_value;
volatile short head = 0 ; 
volatile short tail = 0 ; 
volatile unsigned short queue[QUEUE_SIZE] ; 
volatile unsigned char state = START ; 
volatile unsigned char packet_state = PACKET_START ; 
volatile unsigned short cnt = 0 ; 

void queue_init()
{
    head = 0 ; 
    tail = 0 ; 
}

unsigned char is_empty()
{
    return head == tail  ;
}

unsigned char is_full()
{
    return head == (tail + 1) % QUEUE_SIZE ; 
}

void add(unsigned short value)
{
    if (is_full())
    {
#ifdef DEBUG
       write_string("Queue is full!") ;  
#endif
        return ; 
    }
    else
    {
        queue[tail] = value ; 
        tail = (tail + 1) % QUEUE_SIZE ; 
    }
}

unsigned short dequeue()
{
    if (is_empty())
    {
#ifdef DEBUG
       write_string("Queue is empty!") ;  
#endif
        return 0;
    }
    else
    {
        unsigned short value = queue[head] ; 
        head = (head + 1) % QUEUE_SIZE ; 
        return value ; 
    }
}

void adc_init()
{
    ADMUX = 0;
    ADMUX |= (1 << REFS0);  
    ADCSRA |= (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);
    //ADCSRA |= (1 << ADATE);
    ADCSRB = 0; 
    ADCSRA |= (1 << ADEN);
    ADCSRA |= (1 << ADIE);
    sei() ; 
}

void timer_init(unsigned int freq)
{
    float count = (FOSC / 1024.0) / (float)freq - 1 ;
    OCR1A = ((int)count) ;
    TIMSK1 |= (1 << OCIE1A);
    TCCR1B |= (1 << WGM12);
    TCCR1B |= (1 << CS12) | (1 << CS10); // /1024 prescaler
    sei();
}

void uart_timer_init(float freq)
{
	float count = ((FOSC / 256.0) * (float)freq) - 1 ;
	OCR2A = (int) count ;
	TCCR2A |= (1 << WGM21);
	TCCR2B |= (1 << CS21) | (1 << CS22);
	TIMSK2 |= (1 << OCIE2A);
	sei();
}

void usart_init()
{
    UBRR0H = (unsigned char)(BAUDRATE>>8);
    UBRR0L = (unsigned char)BAUDRATE; 
    UCSR0B |= (1<<TXEN0)|(1<<RXEN0);
    UCSR0C = (3<<UCSZ00);
}

void usart_transmit(unsigned char data)
{
    while ( !( UCSR0A & (1<<UDRE0)) ) ;
    UDR0 = data;
}

unsigned char usart_read()
{
    while ( !(UCSR0A & (1 << RXC0)) ) ;
    return UDR0 ; 
}

void write_string(char *string)
{
    unsigned short i = 0 ;
    unsigned short length = strlen(string) ;  
    for (i=0; i < length; i++)
    {
        usart_transmit(string[i]) ; 
    }
}

int main(void)
{
    queue_init() ;
    usart_init() ;
    state = RUNNING ; 
    packet_state = PACKET_START ; 
    adc_init() ; 
    timer_init(1000) ; 
	uart_timer_init(0.0005) ; 
    while (1)
    {
       /*
       char string[80] ;
       sprintf(string, "Queue info.. head %d, tail:  %d\n", head, tail) ;
       write_string(string) ;
       unsigned char code = usart_read() ; 
       if (code == START_MAGIC)
       {
           state = RUNNING ; 
           adc_init() ;
           timer_init(100) ;
       }
       */
       _delay_ms(100) ; 
    }
    return 0;
}

ISR (TIMER1_COMPA_vect)
{
    if (state == RUNNING)
    {
        ADCSRA |= (1 << ADSC);
    }
}

volatile unsigned short k = 0 ;
	
ISR(ADC_vect)
{
   volatile unsigned short low = ADCL ; 
   volatile unsigned short high = ADCH ; 
   adc_value = (high << 8) + low ; 
#ifdef ADC_DEBUG
   add(k) ;
   k++ ;
   if (k == 1024) k = 0 ;
#else
   add(adc_value) ; 
#endif
}

ISR (TIMER2_COMPA_vect)
{
    if (packet_state == PACKET_START)
    {
        usart_transmit(PACKET_START_MAGIC) ;
        packet_state = PACKET_SIZE ;
        cnt = 0 ;  
        return ;  
    }
    if (packet_state == PACKET_DATA)
    {
        if (cnt < NUMBER_VALUES)
        {
            if (!is_empty())
            {
                unsigned short value = dequeue() ;  
                unsigned char low = (value & 0x00FF) ; 
                unsigned char high = ((value & 0xFF00) >> 8) ; 
                usart_transmit(low) ; 
                usart_transmit(high) ; 
                cnt++ ; 
            }
        }
        else
        {
            packet_state = PACKET_END ; 
            cnt = 0 ; 
        }
        return  ; 
    }
    if (packet_state == PACKET_END)
    {
        packet_state = PACKET_START ; 
        usart_transmit(PACKET_END_MAGIC) ; 
        return ; 
    }
    if (packet_state == PACKET_SIZE)
    {
        unsigned char size_low = (NUMBER_VALUES & 0x00FF) ; 
        unsigned char size_high = ((NUMBER_VALUES & 0xFF00) >> 8) ;  
        usart_transmit(size_low) ; 
        usart_transmit(size_high) ; 
        packet_state = PACKET_DATA ;
        return ;  
    }
}
