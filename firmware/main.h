/**

*/

void queue_init() ; 
unsigned char is_empty() ;
unsigned char is_full() ;
unsigned short dequeue() ; 
void add(unsigned short value) ;
void adc_init() ;
void timer_init(unsigned int freq) ;
void usart_init() ;
void usart_transmit(unsigned char data) ; 
void write_string(char *string) ;
