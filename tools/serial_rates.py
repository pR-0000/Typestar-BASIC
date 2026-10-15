"""SCI settings: rates since .45/.47, seven-bit parity/stop selection since .46."""
BAUD_RATES=(1200,2400,7812,15625,31250)

def add_baud_argument(parser):
    parser.add_argument('--baud',type=int,choices=BAUD_RATES,default=31250,
        help='Set matching BAUD on Canon (default %(default)s; 2400/7812: .45+, 15625/31250: .47+)')
    parser.add_argument('--parity',type=str.upper,choices=('N','E','O'),default='E',
        help='Parity: none/even/odd; set matching SERCFG 7xx on firmware .46+')
    parser.add_argument('--stopbits',type=int,choices=(1,2),default=1,
        help='Stop bits (default 1); set matching SERCFG 7xx on firmware .46+')

def bits_per_frame(parity='E',stopbits=1):
    return 1+7+(parity!='N')+stopbits
